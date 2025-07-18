"""
ADK Agent Log Analyzer with Pattern Detection

Analyzes parsed log data to identify:
- Rate limit issues
- Performance bottlenecks
- Error patterns
- Query optimization opportunities
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter, defaultdict

from log_parser import ADKLogParser, ParsedSession, SPARQLQuery


@dataclass
class RateLimitAnalysis:
    """Analysis of rate limit patterns"""
    total_requests: int
    duration_minutes: float
    requests_per_minute: float
    peak_rpm: float
    peak_time: Optional[datetime] = None
    approaching_limit: bool = False
    hit_limit: bool = False
    recommended_throttle_ms: int = 0


@dataclass
class QueryAnalysis:
    """Analysis of SPARQL query patterns"""
    total_queries: int
    success_rate: float
    failed_queries: List[SPARQLQuery] = field(default_factory=list)
    slow_queries: List[Tuple[SPARQLQuery, float]] = field(default_factory=list)
    large_result_queries: List[SPARQLQuery] = field(default_factory=list)
    most_common_errors: List[Tuple[str, int]] = field(default_factory=list)
    optimization_suggestions: List[str] = field(default_factory=list)


@dataclass
class ConversationAnalysis:
    """Analysis of conversation patterns"""
    total_turns: int
    avg_tokens_per_turn: float
    function_call_frequency: Dict[str, int] = field(default_factory=dict)
    agent_transfers: int = 0
    conversation_flow: List[str] = field(default_factory=list)


@dataclass
class AnalysisReport:
    """Complete analysis report"""
    session_id: str
    rate_limit: RateLimitAnalysis
    queries: QueryAnalysis
    conversation: ConversationAnalysis
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ADKLogAnalyzer:
    """Analyzer for ADK agent logs"""
    
    # Rate limits based on Vertex AI documentation
    VERTEX_AI_RPM_LIMIT = 60  # Requests per minute limit
    VERTEX_AI_RPM_WARNING = 45  # Warning threshold
    
    def __init__(self):
        self.large_result_threshold = 1000  # Rows
        self.slow_query_threshold = 5.0  # Seconds
        
    def analyze_session(self, session: ParsedSession) -> AnalysisReport:
        """Analyze a single session"""
        rate_limit = self._analyze_rate_limits(session)
        queries = self._analyze_queries(session)
        conversation = self._analyze_conversation(session)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(rate_limit, queries, conversation)
        warnings = self._generate_warnings(rate_limit, queries, session)
        
        return AnalysisReport(
            session_id=session.session_id,
            rate_limit=rate_limit,
            queries=queries,
            conversation=conversation,
            recommendations=recommendations,
            warnings=warnings
        )
    
    def _analyze_rate_limits(self, session: ParsedSession) -> RateLimitAnalysis:
        """Analyze rate limit patterns"""
        if not session.request_count:
            return RateLimitAnalysis(
                total_requests=0,
                duration_minutes=0,
                requests_per_minute=0,
                peak_rpm=0
            )
        
        duration = (session.end_time or datetime.now()) - session.start_time
        duration_minutes = duration.total_seconds() / 60
        
        # Calculate overall rate
        rpm = session.request_count / duration_minutes if duration_minutes > 0 else 0
        
        # Find peak rate (using 1-minute windows)
        request_times = []
        
        # Estimate request times from conversation turns and queries
        if session.conversation_turns:
            request_times.extend([turn.timestamp for turn in session.conversation_turns])
        
        peak_rpm = self._calculate_peak_rate(request_times) if request_times else rpm
        
        # Check if we hit or are approaching limits
        hit_limit = any(error.get('message', '').find('429') >= 0 for error in session.errors)
        approaching_limit = peak_rpm >= self.VERTEX_AI_RPM_WARNING
        
        # Calculate recommended throttle
        recommended_throttle = 0
        if approaching_limit or hit_limit:
            # Target 80% of limit for safety
            target_rpm = self.VERTEX_AI_RPM_LIMIT * 0.8
            recommended_throttle = int(60000 / target_rpm)  # milliseconds between requests
        
        return RateLimitAnalysis(
            total_requests=session.request_count,
            duration_minutes=duration_minutes,
            requests_per_minute=rpm,
            peak_rpm=peak_rpm,
            peak_time=None,  # TODO: track actual peak time
            approaching_limit=approaching_limit,
            hit_limit=hit_limit,
            recommended_throttle_ms=recommended_throttle
        )
    
    def _calculate_peak_rate(self, timestamps: List[datetime]) -> float:
        """Calculate peak requests per minute"""
        if len(timestamps) < 2:
            return 0
        
        timestamps = sorted(timestamps)
        max_count = 0
        
        # Sliding window of 1 minute
        for i, start_time in enumerate(timestamps):
            end_time = start_time + timedelta(minutes=1)
            count = sum(1 for t in timestamps if start_time <= t < end_time)
            max_count = max(max_count, count)
        
        return float(max_count)
    
    def _analyze_queries(self, session: ParsedSession) -> QueryAnalysis:
        """Analyze SPARQL query patterns"""
        if not session.sparql_queries:
            return QueryAnalysis(total_queries=0, success_rate=0)
        
        total = len(session.sparql_queries)
        successful = sum(1 for q in session.sparql_queries if q.success)
        
        # Find failed queries
        failed_queries = [q for q in session.sparql_queries if not q.success]
        
        # Find large result queries
        large_queries = [
            q for q in session.sparql_queries 
            if q.row_count > self.large_result_threshold
        ]
        
        # Count error types
        error_counter = Counter(q.error for q in failed_queries if q.error)
        most_common_errors = error_counter.most_common(5)
        
        # Generate optimization suggestions
        suggestions = self._generate_query_suggestions(session.sparql_queries)
        
        return QueryAnalysis(
            total_queries=total,
            success_rate=successful / total if total > 0 else 0,
            failed_queries=failed_queries[:10],  # Top 10
            slow_queries=[],  # TODO: track query execution time
            large_result_queries=large_queries[:10],
            most_common_errors=most_common_errors,
            optimization_suggestions=suggestions
        )
    
    def _generate_query_suggestions(self, queries: List[SPARQLQuery]) -> List[str]:
        """Generate query optimization suggestions"""
        suggestions = []
        
        # Check for missing LIMIT clauses
        unlimited_queries = sum(
            1 for q in queries 
            if q.success and q.row_count > 100 and 'LIMIT' not in q.query.upper()
        )
        if unlimited_queries > 0:
            suggestions.append(
                f"Add LIMIT clauses: {unlimited_queries} queries returned >100 rows without LIMIT"
            )
        
        # Check for repeated failed patterns
        failed_patterns = defaultdict(int)
        for q in queries:
            if not q.success and q.error:
                if "prefix" in q.error.lower():
                    failed_patterns['prefix_errors'] += 1
                elif "angle bracket" in q.error.lower():
                    failed_patterns['angle_bracket_errors'] += 1
        
        if failed_patterns['prefix_errors'] > 0:
            suggestions.append(
                f"Fix prefix usage: {failed_patterns['prefix_errors']} queries failed due to prefix issues"
            )
        
        if failed_patterns['angle_bracket_errors'] > 0:
            suggestions.append(
                f"Remove angle brackets: {failed_patterns['angle_bracket_errors']} queries failed due to angle brackets"
            )
        
        # Check for inefficient patterns
        equipment_queries = [q for q in queries if 'Equipment' in q.query]
        if len(equipment_queries) > 10:
            suggestions.append(
                "Consider caching equipment data - queried >10 times in session"
            )
        
        return suggestions
    
    def _analyze_conversation(self, session: ParsedSession) -> ConversationAnalysis:
        """Analyze conversation patterns"""
        if not session.conversation_turns:
            return ConversationAnalysis(
                total_turns=0,
                avg_tokens_per_turn=0
            )
        
        total_turns = len(session.conversation_turns)
        total_tokens = sum(
            turn.token_usage.get('totalTokenCount', 0) 
            for turn in session.conversation_turns 
            if turn.token_usage
        )
        
        # Count function calls
        function_calls = Counter()
        agent_transfers = 0
        
        for turn in session.conversation_turns:
            for call in turn.function_calls:
                func_name = call.get('name', 'unknown')
                function_calls[func_name] += 1
                if func_name == 'transfer_to_agent':
                    agent_transfers += 1
        
        # Extract conversation flow
        flow = []
        for turn in session.conversation_turns[:10]:  # First 10 turns
            if turn.content:
                summary = turn.content[:50] + "..." if len(turn.content) > 50 else turn.content
                flow.append(f"{turn.role}: {summary}")
        
        return ConversationAnalysis(
            total_turns=total_turns,
            avg_tokens_per_turn=total_tokens / total_turns if total_turns > 0 else 0,
            function_call_frequency=dict(function_calls),
            agent_transfers=agent_transfers,
            conversation_flow=flow
        )
    
    def _generate_recommendations(self, rate_limit: RateLimitAnalysis, 
                                 queries: QueryAnalysis,
                                 conversation: ConversationAnalysis) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Rate limit recommendations
        if rate_limit.hit_limit:
            recommendations.append(
                f"CRITICAL: Implement request throttling of {rate_limit.recommended_throttle_ms}ms between requests"
            )
        elif rate_limit.approaching_limit:
            recommendations.append(
                f"WARNING: Approaching rate limit. Consider throttling to {rate_limit.recommended_throttle_ms}ms"
            )
        
        # Query recommendations
        if queries.success_rate < 0.5:
            recommendations.append(
                f"Low query success rate ({queries.success_rate:.1%}). Review query patterns and fix common errors"
            )
        
        if queries.large_result_queries:
            recommendations.append(
                f"Optimize large queries: {len(queries.large_result_queries)} queries returned >{self.large_result_threshold} rows"
            )
        
        # Add query-specific suggestions
        recommendations.extend(queries.optimization_suggestions)
        
        # Conversation recommendations
        if conversation.avg_tokens_per_turn > 10000:
            recommendations.append(
                "High token usage per turn. Consider reducing context size or response length"
            )
        
        if conversation.agent_transfers > 5:
            recommendations.append(
                "High agent transfer count. Consider consolidating agent responsibilities"
            )
        
        return recommendations
    
    def _generate_warnings(self, rate_limit: RateLimitAnalysis,
                          queries: QueryAnalysis,
                          session: ParsedSession) -> List[str]:
        """Generate warnings for critical issues"""
        warnings = []
        
        if rate_limit.hit_limit:
            warnings.append("🚨 RATE LIMIT HIT: Service returned 429 error")
        
        if session.errors:
            for error in session.errors:
                if "RESOURCE_EXHAUSTED" in error.get('message', ''):
                    warnings.append("🚨 RESOURCE EXHAUSTED: Quota limit reached")
                elif "Failed to detach context" in error.get('message', ''):
                    warnings.append("⚠️  Context detachment error - possible memory issue")
        
        if queries.success_rate < 0.25:
            warnings.append("⚠️  Very low query success rate - check SPARQL syntax")
        
        return warnings
    
    def generate_report(self, analysis: AnalysisReport) -> str:
        """Generate a human-readable report"""
        lines = []
        
        lines.append(f"=== Analysis Report for Session {analysis.session_id} ===\n")
        
        # Warnings
        if analysis.warnings:
            lines.append("⚠️  WARNINGS:")
            for warning in analysis.warnings:
                lines.append(f"  {warning}")
            lines.append("")
        
        # Rate Limit Analysis
        lines.append("📊 Rate Limit Analysis:")
        lines.append(f"  Total Requests: {analysis.rate_limit.total_requests}")
        lines.append(f"  Duration: {analysis.rate_limit.duration_minutes:.2f} minutes")
        lines.append(f"  Average RPM: {analysis.rate_limit.requests_per_minute:.2f}")
        lines.append(f"  Peak RPM: {analysis.rate_limit.peak_rpm:.2f}")
        if analysis.rate_limit.hit_limit:
            lines.append(f"  ❌ HIT RATE LIMIT")
        elif analysis.rate_limit.approaching_limit:
            lines.append(f"  ⚠️  Approaching rate limit")
        else:
            lines.append(f"  ✅ Within rate limits")
        lines.append("")
        
        # Query Analysis
        lines.append("🔍 Query Analysis:")
        lines.append(f"  Total Queries: {analysis.queries.total_queries}")
        lines.append(f"  Success Rate: {analysis.queries.success_rate:.1%}")
        if analysis.queries.large_result_queries:
            lines.append(f"  Large Results: {len(analysis.queries.large_result_queries)} queries")
        if analysis.queries.most_common_errors:
            lines.append("  Common Errors:")
            for error, count in analysis.queries.most_common_errors[:3]:
                lines.append(f"    - {error[:50]}... ({count} times)")
        lines.append("")
        
        # Conversation Analysis
        lines.append("💬 Conversation Analysis:")
        lines.append(f"  Total Turns: {analysis.conversation.total_turns}")
        lines.append(f"  Avg Tokens/Turn: {analysis.conversation.avg_tokens_per_turn:.0f}")
        lines.append(f"  Agent Transfers: {analysis.conversation.agent_transfers}")
        if analysis.conversation.function_call_frequency:
            lines.append("  Function Calls:")
            for func, count in sorted(analysis.conversation.function_call_frequency.items(), 
                                     key=lambda x: x[1], reverse=True)[:3]:
                lines.append(f"    - {func}: {count}")
        lines.append("")
        
        # Recommendations
        if analysis.recommendations:
            lines.append("💡 Recommendations:")
            for i, rec in enumerate(analysis.recommendations, 1):
                lines.append(f"  {i}. {rec}")
        
        return "\n".join(lines)


def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python log_analyzer.py <log_file_path>")
        sys.exit(1)
    
    log_path = Path(sys.argv[1])
    
    # Parse log file
    parser = ADKLogParser()
    sessions = parser.parse_log_file(log_path)
    
    if not sessions:
        print("No sessions found in log file")
        sys.exit(1)
    
    # Analyze each session
    analyzer = ADKLogAnalyzer()
    
    for session_id, session in sessions.items():
        analysis = analyzer.analyze_session(session)
        report = analyzer.generate_report(analysis)
        print(report)
        print("\n" + "="*60 + "\n")
        
        # Save detailed analysis as JSON
        output_path = log_path.with_suffix('.analysis.json')
        with open(output_path, 'w') as f:
            json.dump({
                'session_id': analysis.session_id,
                'rate_limit': {
                    'total_requests': analysis.rate_limit.total_requests,
                    'duration_minutes': analysis.rate_limit.duration_minutes,
                    'requests_per_minute': analysis.rate_limit.requests_per_minute,
                    'peak_rpm': analysis.rate_limit.peak_rpm,
                    'hit_limit': analysis.rate_limit.hit_limit,
                    'recommended_throttle_ms': analysis.rate_limit.recommended_throttle_ms
                },
                'queries': {
                    'total': analysis.queries.total_queries,
                    'success_rate': analysis.queries.success_rate,
                    'failed_count': len(analysis.queries.failed_queries),
                    'large_result_count': len(analysis.queries.large_result_queries),
                    'optimization_suggestions': analysis.queries.optimization_suggestions
                },
                'warnings': analysis.warnings,
                'recommendations': analysis.recommendations
            }, f, indent=2)
        
        print(f"Detailed analysis saved to: {output_path}")


if __name__ == "__main__":
    main()