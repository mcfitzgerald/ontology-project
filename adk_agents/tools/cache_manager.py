"""Cache management for query patterns and results."""
import json
import os
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
        self.query_cache_file = CACHE_DIR / "query_cache.json"
        self.successful_patterns_file = CACHE_DIR / "successful_patterns.json"
        self.size_warning_threshold_mb = 100  # Warn at 100MB
        self.size_critical_threshold_mb = 500  # Critical at 500MB
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
        
        self.save_stats_with_size_check()
    
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
    
    def get_file_size_mb(self, file_path: Path) -> float:
        """Get file size in megabytes."""
        if file_path.exists():
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 * 1024)
        return 0.0
    
    def check_cache_size(self) -> Dict[str, float]:
        """Check sizes of all cache files and emit warnings if needed."""
        sizes = {
            "query_cache": self.get_file_size_mb(self.query_cache_file),
            "successful_patterns": self.get_file_size_mb(self.successful_patterns_file),
            "cache_stats": self.get_file_size_mb(self.stats_file),
            "query_patterns": self.get_file_size_mb(self.patterns_file)
        }
        
        total_size = sum(sizes.values())
        
        # Check query cache specifically since it tends to be the largest
        if sizes["query_cache"] > self.size_warning_threshold_mb:
            logger.warning(
                f"Cache file 'query_cache.json' size ({sizes['query_cache']:.1f}MB) "
                f"exceeds recommended limit ({self.size_warning_threshold_mb}MB)"
            )
        
        if total_size > self.size_critical_threshold_mb:
            logger.warning(
                f"Total cache size ({total_size:.1f}MB) exceeds critical limit "
                f"({self.size_critical_threshold_mb}MB). Consider clearing cache."
            )
        
        return sizes
    
    def clear_cache(self, clear_patterns: bool = False):
        """Clear cache files."""
        try:
            # Always clear the main query cache
            if self.query_cache_file.exists():
                self.query_cache_file.unlink()
                logger.info(f"Cleared query cache file: {self.query_cache_file}")
            
            # Optionally clear patterns
            if clear_patterns:
                if self.successful_patterns_file.exists():
                    self.successful_patterns_file.unlink()
                    logger.info(f"Cleared successful patterns file: {self.successful_patterns_file}")
                
                # Reset in-memory patterns
                self.patterns = {
                    "capacity": [],
                    "temporal": [],
                    "quality": [],
                    "financial": [],
                    "aggregation": []
                }
                self.save_stats_with_size_check()
            
            # Reset stats
            self.stats = defaultdict(int)
            self.save_stats_with_size_check()
            
            logger.info("Cache cleared successfully")
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def save_stats_with_size_check(self):
        """Save stats with automatic size checking."""
        # Check size before saving
        sizes = self.check_cache_size()
        
        # If critical threshold exceeded, log but still save
        # (user can manually clear if needed)
        if sum(sizes.values()) > self.size_critical_threshold_mb:
            logger.warning("Cache size exceeds critical threshold. Consider using clear_cache().")
        
        # Call original save_stats logic
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(dict(self.stats), f, indent=2)
            
            with open(self.patterns_file, 'w') as f:
                json.dump(self.patterns, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")

# Create singleton instance
cache_manager = CacheManager()