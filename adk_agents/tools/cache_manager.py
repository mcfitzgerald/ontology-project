"""Cache management for query patterns and results."""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from collections import defaultdict

from ..config.settings import CACHE_DIR, CACHE_TTL, CACHE_MAX_SIZE

logger = logging.getLogger(__name__)

class CacheManager:
    """Manages query caching and pattern learning."""
    
    def __init__(self):
        self.stats_file = CACHE_DIR / "cache_stats.json"
        self.patterns_file = CACHE_DIR / "query_patterns.json"
        self.load_stats()
    
    def load_stats(self):
        """Load cache statistics and patterns."""
        self.stats = defaultdict(int)
        self.patterns = {
            "capacity": [],
            "temporal": [],
            "quality": [],
            "financial": [],
            "aggregation": []
        }
        
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    self.stats.update(json.load(f))
            except Exception as e:
                logger.warning(f"Failed to load stats: {e}")
        
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r') as f:
                    self.patterns.update(json.load(f))
            except Exception as e:
                logger.warning(f"Failed to load patterns: {e}")
    
    def save_stats(self):
        """Save cache statistics and patterns."""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(dict(self.stats), f, indent=2)
            
            with open(self.patterns_file, 'w') as f:
                json.dump(self.patterns, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")
    
    def classify_query(self, query: str) -> str:
        """Classify query type based on content."""
        query_upper = query.upper()
        
        # Check for specific patterns
        if any(term in query_upper for term in ["OEE", "AVAILABILITY", "PERFORMANCE"]):
            return "capacity"
        elif any(term in query_upper for term in ["DATE", "TIME", "PERIOD", "TREND"]):
            return "temporal"
        elif any(term in query_upper for term in ["QUALITY", "DEFECT", "REJECTION"]):
            return "quality"
        elif any(term in query_upper for term in ["COST", "REVENUE", "ROI", "FINANCIAL"]):
            return "financial"
        elif any(term in query_upper for term in ["AVG", "SUM", "COUNT", "MIN", "MAX"]):
            return "aggregation"
        else:
            return "general"
    
    def record_query(self, query: str, success: bool, result_count: int = 0):
        """Record query execution statistics."""
        query_type = self.classify_query(query)
        
        # Update stats
        self.stats["total_queries"] += 1
        self.stats[f"{query_type}_queries"] += 1
        
        if success:
            self.stats["successful_queries"] += 1
            self.stats[f"{query_type}_success"] += 1
            
            # Save successful pattern
            if query_type in self.patterns:
                pattern = {
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "result_count": result_count
                }
                self.patterns[query_type].append(pattern)
                
                # Keep only recent patterns
                cutoff_time = datetime.now() - timedelta(days=7)
                self.patterns[query_type] = [
                    p for p in self.patterns[query_type]
                    if datetime.fromisoformat(p["timestamp"]) > cutoff_time
                ][:50]  # Keep max 50 patterns per type
        else:
            self.stats["failed_queries"] += 1
        
        self.save_stats()
    
    def get_success_rate(self, query_type: Optional[str] = None) -> float:
        """Get success rate for queries."""
        if query_type:
            total = self.stats.get(f"{query_type}_queries", 0)
            success = self.stats.get(f"{query_type}_success", 0)
        else:
            total = self.stats.get("total_queries", 0)
            success = self.stats.get("successful_queries", 0)
        
        return (success / total * 100) if total > 0 else 0.0
    
    def get_similar_patterns(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar successful query patterns."""
        query_type = self.classify_query(query)
        patterns = self.patterns.get(query_type, [])
        
        # Sort by recency
        patterns.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return patterns[:limit]
    
    def cleanup_old_cache(self, cache_files: List[Path]):
        """Clean up old cache files based on TTL."""
        cutoff_time = datetime.now() - timedelta(seconds=CACHE_TTL)
        
        for cache_file in cache_files:
            if cache_file.exists():
                # Check file modification time
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if mtime < cutoff_time:
                    try:
                        cache_file.unlink()
                        logger.info(f"Removed old cache file: {cache_file}")
                    except Exception as e:
                        logger.error(f"Failed to remove cache file: {e}")
    
    def get_cache_summary(self) -> Dict[str, Any]:
        """Get cache statistics summary."""
        return {
            "total_queries": self.stats.get("total_queries", 0),
            "successful_queries": self.stats.get("successful_queries", 0),
            "failed_queries": self.stats.get("failed_queries", 0),
            "success_rate": self.get_success_rate(),
            "pattern_counts": {
                pattern_type: len(patterns)
                for pattern_type, patterns in self.patterns.items()
            },
            "query_type_stats": {
                query_type: {
                    "total": self.stats.get(f"{query_type}_queries", 0),
                    "success_rate": self.get_success_rate(query_type)
                }
                for query_type in ["capacity", "temporal", "quality", "financial", "aggregation"]
            }
        }

# Create singleton instance
cache_manager = CacheManager()