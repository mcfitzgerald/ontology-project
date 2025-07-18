"""
ADK Agent Log Parser with Smart Data Truncation

Parses ADK web logs to extract meaningful diagnostic information while:
- Filtering out redundant context and system prompts
- Truncating large SPARQL query results
- Preserving essential debugging information
"""

import re
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LogEntry:
    """Represents a parsed log entry"""
    timestamp: datetime
    level: str
    module: str
    message: str
    raw_line: str
    line_number: int


@dataclass
class ConversationTurn:
    """Represents a conversation turn between user and agent"""
    timestamp: datetime
    role: str
    content: str
    author: Optional[str] = None
    function_calls: List[Dict] = field(default_factory=list)
    token_usage: Optional[Dict] = None


@dataclass
class SPARQLQuery:
    """Represents a SPARQL query and its result"""
    timestamp: datetime
    query: str
    purpose: Optional[str] = None
    success: bool = False
    row_count: int = 0
    results_truncated: List[List[Any]] = field(default_factory=list)
    results_hash: Optional[str] = None
    cached: bool = False
    error: Optional[str] = None


@dataclass
class ParsedSession:
    """Represents a parsed agent session"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    conversation_turns: List[ConversationTurn] = field(default_factory=list)
    sparql_queries: List[SPARQLQuery] = field(default_factory=list)
    errors: List[Dict] = field(default_factory=list)
    total_tokens: int = 0
    request_count: int = 0


class ADKLogParser:
    """Parser for ADK agent logs with smart truncation"""
    
    def __init__(self, max_result_rows: int = 10, max_content_length: int = 1000):
        self.max_result_rows = max_result_rows
        self.max_content_length = max_content_length
        
        # Regex patterns
        self.timestamp_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})')
        self.log_level_pattern = re.compile(r' - (DEBUG|INFO|WARNING|ERROR|CRITICAL) - ')
        self.module_pattern = re.compile(r' - (\w+\.py):(\d+) - ')
        self.session_pattern = re.compile(r'sessions/([a-f0-9-]+)')
        self.token_usage_pattern = re.compile(r'"totalTokenCount":(\d+)')
        
    def parse_log_file(self, log_path: Path) -> Dict[str, ParsedSession]:
        """Parse an ADK log file and return structured data"""
        sessions = {}
        current_session = None
        default_session_id = "default"
        
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        i = 0
        entry_count = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Parse log entry
            entry = self._parse_log_entry(line, i)
            if entry:
                entry_count += 1
            
            # Look for session creation or reference
            if entry:
                if "New session created" in entry.message:
                    session_match = self.session_pattern.search(line)
                    if session_match:
                        session_id = session_match.group(1)
                        current_session = ParsedSession(
                            session_id=session_id,
                            start_time=entry.timestamp
                        )
                        sessions[session_id] = current_session
                elif not current_session and "/sessions/" in line:
                    # Try to find session ID in any line if we don't have one yet
                    session_match = self.session_pattern.search(line)
                    if session_match:
                        session_id = session_match.group(1)
                        current_session = ParsedSession(
                            session_id=session_id,
                            start_time=entry.timestamp
                        )
                        sessions[session_id] = current_session
            
            # Look for LLM requests/responses
            if entry and "Sending out request, model:" in entry.message:
                # Create default session if needed
                if not current_session:
                    current_session = ParsedSession(
                        session_id=default_session_id,
                        start_time=entry.timestamp
                    )
                    sessions[default_session_id] = current_session
                
                # Skip to actual LLM Request line
                while i < len(lines) and "LLM Request:" not in lines[i]:
                    i += 1
                
                # Skip the large context blocks
                i = self._skip_context_block(lines, i)
                current_session.request_count += 1
            
            if entry and "LLM Response:" in line:
                # Parse the response
                timestamp = entry.timestamp if entry else current_session.start_time if current_session else datetime.now()
                i, turn = self._parse_llm_response(lines, i, timestamp)
                if current_session and turn:
                    current_session.conversation_turns.append(turn)
                    if turn.token_usage:
                        current_session.total_tokens += turn.token_usage.get('totalTokenCount', 0)
            
            # Look for SPARQL queries
            elif "execute_sparql_query" in line:
                sparql_query = self._parse_sparql_query(line, lines, i, entry)
                if current_session and sparql_query:
                    current_session.sparql_queries.append(sparql_query)
            
            # Look for errors
            elif entry and entry.level == "ERROR":
                error_info = self._parse_error(lines, i, entry)
                if current_session and error_info:
                    current_session.errors.append(error_info)
                    # Check for session end on critical errors
                    if "RESOURCE_EXHAUSTED" in error_info.get('message', ''):
                        current_session.end_time = entry.timestamp
            
            i += 1
        
        return sessions
    
    def _parse_log_entry(self, line: str, line_number: int) -> Optional[LogEntry]:
        """Parse a single log line into a LogEntry"""
        timestamp_match = self.timestamp_pattern.match(line)
        if not timestamp_match:
            return None
        
        timestamp_str = timestamp_match.group(1)
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
        
        level_match = self.log_level_pattern.search(line)
        level = level_match.group(1) if level_match else "INFO"
        
        module_match = self.module_pattern.search(line)
        module = module_match.group(1) if module_match else "unknown"
        
        # Extract message (everything after module)
        message_start = module_match.end() if module_match else len(timestamp_str) + 3
        message = line[message_start:].strip()
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            module=module,
            message=message,
            raw_line=line,
            line_number=line_number
        )
    
    def _skip_context_block(self, lines: List[str], start_idx: int) -> int:
        """Skip large context blocks to avoid parsing redundant data"""
        i = start_idx + 1
        
        # Look for the end of the context block
        while i < len(lines):
            if "Contents:" in lines[i] or "Functions:" in lines[i]:
                break
            i += 1
        
        return i - 1
    
    def _parse_llm_response(self, lines: List[str], start_idx: int, 
                           timestamp: datetime) -> Tuple[int, Optional[ConversationTurn]]:
        """Parse LLM response including text and function calls"""
        i = start_idx + 1
        text_content = []
        function_calls = []
        token_usage = None
        
        # Look for response content
        while i < len(lines):
            line = lines[i].strip()
            
            if line == "Text:":
                i += 1
                # Collect text until we hit separator
                while i < len(lines) and not lines[i].startswith("---"):
                    text_content.append(lines[i].rstrip())
                    i += 1
            
            elif line == "Function calls:":
                i += 1
                # Parse function calls
                while i < len(lines) and not lines[i].startswith("---"):
                    if "name:" in lines[i]:
                        func_match = re.search(r'name: (\w+), args: ({.*})', lines[i])
                        if func_match:
                            function_calls.append({
                                'name': func_match.group(1),
                                'args': json.loads(func_match.group(2))
                            })
                    i += 1
            
            elif "usage_metadata" in line:
                # Extract token usage
                token_match = self.token_usage_pattern.search(line)
                if token_match:
                    token_usage = {'totalTokenCount': int(token_match.group(1))}
            
            elif "Raw response:" in line or "---" in line:
                break
            
            i += 1
        
        # Create conversation turn
        if text_content or function_calls:
            content = self._truncate_content('\n'.join(text_content))
            return i, ConversationTurn(
                timestamp=timestamp,
                role='assistant',
                content=content,
                function_calls=function_calls,
                token_usage=token_usage
            )
        
        return i, None
    
    def _parse_sparql_query(self, line: str, lines: List[str], start_idx: int,
                           entry: Optional[LogEntry]) -> Optional[SPARQLQuery]:
        """Parse SPARQL query and its result"""
        # Extract query from function call
        query_match = re.search(r"'query':\s*'([^']+)'", line)
        purpose_match = re.search(r"'purpose':\s*'([^']+)'", line)
        
        if not query_match:
            return None
        
        query = query_match.group(1)
        purpose = purpose_match.group(1) if purpose_match else None
        timestamp = entry.timestamp if entry else datetime.now()
        
        # Look for the result in subsequent lines
        i = start_idx + 1
        while i < len(lines) and i < start_idx + 50:  # Look ahead max 50 lines
            if '"success":true' in lines[i] or '"success":false' in lines[i]:
                return self._parse_sparql_result(lines[i], query, purpose, timestamp)
            i += 1
        
        return SPARQLQuery(
            timestamp=timestamp,
            query=query,
            purpose=purpose
        )
    
    def _parse_sparql_result(self, result_line: str, query: str, purpose: Optional[str],
                            timestamp: datetime) -> SPARQLQuery:
        """Parse SPARQL query result with truncation"""
        success_match = re.search(r'"success":(true|false)', result_line)
        success = success_match.group(1) == 'true' if success_match else False
        
        row_count_match = re.search(r'"row_count":(\d+)', result_line)
        row_count = int(row_count_match.group(1)) if row_count_match else 0
        
        cached_match = re.search(r'"cached":(true|false)', result_line)
        cached = cached_match.group(1) == 'true' if cached_match else False
        
        # Extract results
        results_match = re.search(r'"results":\[(.*?)\]', result_line)
        results_truncated = []
        results_hash = None
        
        if results_match and success:
            try:
                # Parse full results
                full_results_str = f'[{results_match.group(1)}]'
                full_results = json.loads(full_results_str)
                
                # Truncate if needed
                if len(full_results) > self.max_result_rows:
                    results_truncated = full_results[:self.max_result_rows]
                    # Create hash of full results for reference
                    results_hash = hashlib.md5(full_results_str.encode()).hexdigest()[:8]
                else:
                    results_truncated = full_results
            except:
                pass
        
        # Extract error if failed
        error = None
        if not success:
            error_match = re.search(r'"error":"([^"]+)"', result_line)
            error = error_match.group(1) if error_match else "Unknown error"
        
        return SPARQLQuery(
            timestamp=timestamp,
            query=query,
            purpose=purpose,
            success=success,
            row_count=row_count,
            results_truncated=results_truncated,
            results_hash=results_hash,
            cached=cached,
            error=error
        )
    
    def _parse_error(self, lines: List[str], start_idx: int, 
                    entry: LogEntry) -> Dict[str, Any]:
        """Parse error information"""
        error_info = {
            'timestamp': entry.timestamp.isoformat(),
            'level': entry.level,
            'message': entry.message,
            'traceback': []
        }
        
        # Look for traceback
        i = start_idx + 1
        while i < len(lines) and i < start_idx + 20:
            if lines[i].startswith('Traceback') or lines[i].startswith('  File'):
                error_info['traceback'].append(lines[i].rstrip())
            elif not lines[i].strip():
                break
            i += 1
        
        return error_info
    
    def _truncate_content(self, content: str) -> str:
        """Truncate long content while preserving key information"""
        if len(content) <= self.max_content_length:
            return content
        
        # Keep beginning and end
        half_length = self.max_content_length // 2
        return f"{content[:half_length]}\n... [truncated {len(content) - self.max_content_length} chars] ...\n{content[-half_length:]}"
    
    def generate_summary(self, sessions: Dict[str, ParsedSession]) -> Dict[str, Any]:
        """Generate a summary of parsed sessions"""
        if not sessions:
            return {
                'session_count': 0,
                'total_requests': 0,
                'total_tokens': 0,
                'total_queries': 0,
                'successful_queries': 0,
                'query_success_rate': 0,
                'duration_minutes': 0,
                'requests_per_minute': 0,
                'errors': 0
            }
        
        total_requests = sum(s.request_count for s in sessions.values())
        total_tokens = sum(s.total_tokens for s in sessions.values())
        total_queries = sum(len(s.sparql_queries) for s in sessions.values())
        successful_queries = sum(
            len([q for q in s.sparql_queries if q.success])
            for s in sessions.values()
        )
        
        # Calculate request rate
        earliest_time = min(s.start_time for s in sessions.values())
        latest_time = max(
            s.end_time or s.start_time 
            for s in sessions.values()
        )
        duration_minutes = (latest_time - earliest_time).total_seconds() / 60
        
        return {
            'session_count': len(sessions),
            'total_requests': total_requests,
            'total_tokens': total_tokens,
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'query_success_rate': successful_queries / total_queries if total_queries > 0 else 0,
            'duration_minutes': duration_minutes,
            'requests_per_minute': total_requests / duration_minutes if duration_minutes > 0 else 0,
            'errors': sum(len(s.errors) for s in sessions.values())
        }


def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python log_parser.py <log_file_path>")
        sys.exit(1)
    
    log_path = Path(sys.argv[1])
    parser = ADKLogParser()
    
    print(f"Parsing log file: {log_path}")
    sessions = parser.parse_log_file(log_path)
    print(f"Found {len(sessions)} sessions")
    
    # Generate summary
    summary = parser.generate_summary(sessions)
    
    print("\n=== Log Summary ===")
    print(f"Sessions: {summary['session_count']}")
    print(f"Total Requests: {summary['total_requests']}")
    print(f"Total Tokens: {summary['total_tokens']:,}")
    print(f"Duration: {summary['duration_minutes']:.2f} minutes")
    print(f"Request Rate: {summary['requests_per_minute']:.2f} req/min")
    print(f"SPARQL Queries: {summary['total_queries']} (Success rate: {summary['query_success_rate']:.1%})")
    print(f"Errors: {summary['errors']}")
    
    # Show session details
    for session_id, session in sessions.items():
        print(f"\n=== Session {session_id} ===")
        print(f"Start: {session.start_time}")
        print(f"End: {session.end_time or 'Active'}")
        print(f"Conversation Turns: {len(session.conversation_turns)}")
        print(f"SPARQL Queries: {len(session.sparql_queries)}")
        print(f"Tokens Used: {session.total_tokens:,}")
        
        if session.errors:
            print(f"\nErrors:")
            for error in session.errors:
                print(f"  - {error['timestamp']}: {error['message'][:100]}...")
        
        # Show sample queries
        if session.sparql_queries:
            print(f"\nSample SPARQL Queries:")
            for query in session.sparql_queries[:3]:
                print(f"  - {query.purpose or 'No purpose'}")
                print(f"    Success: {query.success}, Rows: {query.row_count}")
                if query.results_hash:
                    print(f"    Results truncated (hash: {query.results_hash})")


if __name__ == "__main__":
    main()