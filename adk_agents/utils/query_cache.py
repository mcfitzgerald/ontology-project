"""
Query caching and learning system.
Stores successful patterns and learns from failures.
"""
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

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


class SimpleQueryCache:
    """
    A simple file-based cache for SPARQL query results.
    
    Uses MD5 hashing for query keys and JSON storage with TTL support.
    Designed for prototype systems with moderate query volumes.
    """
    
    def __init__(self, cache_dir: str = "adk_agents/cache/queries", default_ttl_minutes: int = 5):
        """
        Initialize the query cache.
        
        Args:
            cache_dir: Directory to store cached queries
            default_ttl_minutes: Default time-to-live in minutes for cached results
        """
        self.cache_dir = Path(cache_dir)
        self.default_ttl_minutes = default_ttl_minutes
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, query: str) -> str:
        """
        Generate a cache key from the query using MD5 hash.
        
        Args:
            query: SPARQL query string
            
        Returns:
            MD5 hash of the query
        """
        # Normalize query by stripping whitespace and converting to lowercase
        normalized = query.strip().lower()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _get_cache_filepath(self, cache_key: str) -> Path:
        """
        Get the filepath for a cached query.
        
        Args:
            cache_key: MD5 hash key
            
        Returns:
            Path to the cache file
        """
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, query: str, ttl_minutes: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached results for a query if available and not expired.
        
        Args:
            query: SPARQL query string
            ttl_minutes: Override default TTL for this query
            
        Returns:
            Cached results if available and valid, None otherwise
        """
        cache_key = self._get_cache_key(query)
        cache_file = self._get_cache_filepath(cache_key)
        
        # Check if cache file exists
        if not cache_file.exists():
            return None
        
        try:
            # Load cached data
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check timestamp
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            ttl = ttl_minutes if ttl_minutes is not None else self.default_ttl_minutes
            
            if datetime.now() - cached_time > timedelta(minutes=ttl):
                # Cache expired, remove file
                cache_file.unlink()
                return None
            
            return cache_data['results']
            
        except (json.JSONDecodeError, KeyError, ValueError):
            # Invalid cache file, remove it
            cache_file.unlink()
            return None
    
    def set(self, query: str, results: List[Dict[str, Any]]) -> None:
        """
        Cache query results.
        
        Args:
            query: SPARQL query string
            results: Query results to cache
        """
        cache_key = self._get_cache_key(query)
        cache_file = self._get_cache_filepath(cache_key)
        
        cache_data = {
            'query': query,
            'results': results,
            'timestamp': datetime.now().isoformat(),
            'cache_key': cache_key
        }
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            # Log error but don't fail - caching is optional
            print(f"Failed to cache query results: {e}")
    
    def clear(self) -> int:
        """
        Clear all cached queries.
        
        Returns:
            Number of cache files removed
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except Exception:
                pass
        return count
    
    def clear_expired(self, ttl_minutes: Optional[int] = None) -> int:
        """
        Clear only expired cache entries.
        
        Args:
            ttl_minutes: Override default TTL for expiration check
            
        Returns:
            Number of expired cache files removed
        """
        count = 0
        ttl = ttl_minutes if ttl_minutes is not None else self.default_ttl_minutes
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                cached_time = datetime.fromisoformat(cache_data['timestamp'])
                if datetime.now() - cached_time > timedelta(minutes=ttl):
                    cache_file.unlink()
                    count += 1
                    
            except Exception:
                # Invalid cache file, remove it
                try:
                    cache_file.unlink()
                    count += 1
                except Exception:
                    pass
        
        return count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        total_files = 0
        total_size = 0
        expired_count = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            total_files += 1
            total_size += cache_file.stat().st_size
            
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                cached_time = datetime.fromisoformat(cache_data['timestamp'])
                if datetime.now() - cached_time > timedelta(minutes=self.default_ttl_minutes):
                    expired_count += 1
                    
            except Exception:
                expired_count += 1
        
        return {
            'total_cached_queries': total_files,
            'total_cache_size_bytes': total_size,
            'expired_queries': expired_count,
            'cache_directory': str(self.cache_dir.absolute()),
            'default_ttl_minutes': self.default_ttl_minutes
        }