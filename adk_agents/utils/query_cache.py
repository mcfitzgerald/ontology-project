"""
Query caching and learning system.
Stores successful patterns and learns from failures.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

class QueryCache:
    """Learns from query successes and failures."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_file = cache_dir / "query_cache.json"
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load existing cache or create new."""
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {
            "successful_queries": [],
            "failed_queries": [],
            "patterns": {},
            "fixes": {}
        }
    
    def add_success(self, query: str, purpose: str, results: Any, 
                   row_count: int, analysis_type: str = None):
        """Record successful query with metadata."""
        entry = {
            "query": query,
            "purpose": purpose,
            "row_count": row_count,
            "analysis_type": analysis_type,
            "timestamp": datetime.now().isoformat(),
            "pattern": self._extract_pattern(query)
        }
        
        self.cache["successful_queries"].append(entry)
        
        # Update pattern statistics
        pattern = entry["pattern"]
        if pattern not in self.cache["patterns"]:
            self.cache["patterns"][pattern] = {"count": 0, "examples": []}
        
        self.cache["patterns"][pattern]["count"] += 1
        self.cache["patterns"][pattern]["examples"].append({
            "query": query,
            "purpose": purpose,
            "row_count": row_count
        })
        
        self._save_cache()
    
    def add_failure(self, query: str, error: str, fixed_query: Optional[str] = None):
        """Record failed query and potential fix."""
        entry = {
            "query": query,
            "error": error,
            "fixed_query": fixed_query,
            "timestamp": datetime.now().isoformat()
        }
        
        self.cache["failed_queries"].append(entry)
        
        # Learn fix patterns
        if fixed_query and "Unknown prefix" in error:
            self.cache["fixes"]["prefix_errors"] = "Always use mes_ontology_populated:"
        elif fixed_query and "Lexing error" in error:
            self.cache["fixes"]["lexing_errors"] = "Remove angle brackets, use FILTER(ISIRI())"
        
        self._save_cache()
    
    def find_similar_success(self, purpose: str, analysis_type: str = None) -> Optional[Dict]:
        """Find similar successful query by purpose."""
        # Simple keyword matching for now
        # Could use embeddings for better similarity
        keywords = purpose.lower().split()
        
        best_match = None
        best_score = 0
        
        for entry in self.cache["successful_queries"]:
            entry_keywords = entry["purpose"].lower().split()
            score = len(set(keywords) & set(entry_keywords))
            
            if analysis_type and entry.get("analysis_type") == analysis_type:
                score += 2
            
            if score > best_score:
                best_score = score
                best_match = entry
        
        return best_match if best_score > 0 else None
    
    def _extract_pattern(self, query: str) -> str:
        """Extract query pattern for learning."""
        # Simplified pattern extraction
        lines = query.strip().split('\n')
        pattern_parts = []
        
        for line in lines:
            if 'SELECT' in line:
                pattern_parts.append('SELECT')
            elif 'WHERE' in line:
                pattern_parts.append('WHERE')
            elif '?equipment' in line and 'logsEvent' in line:
                pattern_parts.append('equipment->event')
            elif 'GROUP BY' in line:
                pattern_parts.append('GROUP_BY')
            elif 'ORDER BY' in line:
                pattern_parts.append('ORDER_BY')
            elif 'FILTER' in line and 'oee' in line.lower():
                pattern_parts.append('FILTER_OEE')
        
        return '-'.join(pattern_parts)
    
    def _save_cache(self):
        """Persist cache to disk."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "successful_queries": len(self.cache["successful_queries"]),
            "failed_queries": len(self.cache["failed_queries"]),
            "learned_patterns": len(self.cache["patterns"]),
            "known_fixes": len(self.cache["fixes"])
        }