"""Result cache manager for handling large query results."""
import json
import hashlib
import logging
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from pathlib import Path
import uuid

from ..config.settings import CACHE_DIR

logger = logging.getLogger(__name__)

class ResultCacheManager:
    """Manages caching of large query results with summaries."""
    
    def __init__(self):
        self.cache_dir = CACHE_DIR / "results"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.cache_dir / "index.json"
        self.size_warning_threshold_mb = 50  # Warn at 50MB per result file
        self.total_size_warning_threshold_mb = 200  # Warn at 200MB total
        self.load_index()
    
    def load_index(self):
        """Load cache index."""
        self.index = {}
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    self.index = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache index: {e}")
    
    def save_index(self):
        """Save cache index."""
        try:
            # Check size before saving
            self.check_cache_size()
            
            with open(self.index_file, 'w') as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")
    
    def estimate_tokens(self, data: Any) -> int:
        """Estimate token count using simple heuristics.
        
        Rough estimation: 1 token ≈ 4 characters
        This overestimates slightly which is safer.
        """
        if isinstance(data, str):
            return len(data) // 4
        else:
            # Convert to JSON string and estimate
            json_str = json.dumps(data)
            return len(json_str) // 4
    
    def create_summary(self, data: Dict[str, Any], max_rows: int = 10) -> Dict[str, Any]:
        """Create a summary of query results."""
        if "data" not in data or "results" not in data["data"]:
            return data
        
        results = data["data"]["results"]
        columns = data["data"].get("columns", [])
        
        summary = {
            "row_count": len(results),
            "columns": columns,
            "sample_data": results[:max_rows] if len(results) > max_rows else results,
            "estimated_tokens": self.estimate_tokens(results),
            "truncated": len(results) > max_rows
        }
        
        # Add statistics for numeric columns
        if results and columns:
            stats = {}
            for i, col in enumerate(columns):
                values = []
                for row in results:
                    try:
                        val = float(row[i])
                        values.append(val)
                    except (ValueError, TypeError, IndexError):
                        pass
                
                if values:
                    stats[col] = {
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "count": len(values)
                    }
            
            if stats:
                summary["statistics"] = stats
        
        # Add metadata
        if "metadata" in data:
            summary["metadata"] = data["metadata"]
        
        return summary
    
    def cache_result(self, query: str, result: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Cache query result and return cache ID with summary.
        
        Returns:
            Tuple of (cache_id, summary)
        """
        # Generate unique cache ID
        cache_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Save full result to file
        result_file = self.cache_dir / f"{cache_id}.json"
        try:
            with open(result_file, 'w') as f:
                json.dump(result, f)
        except Exception as e:
            logger.error(f"Failed to cache result: {e}")
            return "", result
        
        # Create summary
        summary = self.create_summary(result)
        
        # Update index
        self.index[cache_id] = {
            "query": query,
            "timestamp": timestamp,
            "file": str(result_file),
            "row_count": summary.get("row_count", 0),
            "columns": summary.get("columns", []),
            "estimated_tokens": summary.get("estimated_tokens", 0)
        }
        self.save_index()
        
        # Add cache reference to summary
        summary["cache_id"] = cache_id
        summary["cached_at"] = timestamp
        
        return cache_id, summary
    
    def get_cached_result(self, cache_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full cached result by ID."""
        if cache_id not in self.index:
            return None
        
        result_file = Path(self.index[cache_id]["file"])
        if not result_file.exists():
            return None
        
        try:
            with open(result_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cached result: {e}")
            return None
    
    def list_cached_results(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent cached results."""
        # Sort by timestamp descending
        sorted_items = sorted(
            self.index.items(),
            key=lambda x: x[1]["timestamp"],
            reverse=True
        )[:limit]
        
        return [
            {
                "cache_id": cache_id,
                **info
            }
            for cache_id, info in sorted_items
        ]
    
    def get_file_size_mb(self, file_path: Path) -> float:
        """Get file size in megabytes."""
        if file_path.exists():
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 * 1024)
        return 0.0
    
    def check_cache_size(self) -> Dict[str, Any]:
        """Check sizes of cache files and emit warnings if needed."""
        result = {
            "index_size_mb": self.get_file_size_mb(self.index_file),
            "result_files": [],
            "total_size_mb": 0.0,
            "file_count": 0
        }
        
        # Check all result files
        for cache_id, info in self.index.items():
            # Handle missing 'file' key for backward compatibility
            if "file" not in info:
                logger.warning(f"Cache entry {cache_id} missing 'file' key, skipping")
                continue
                
            result_file = Path(info["file"])
            if result_file.exists():
                size_mb = self.get_file_size_mb(result_file)
                result["result_files"].append({
                    "cache_id": cache_id,
                    "file": str(result_file.name),
                    "size_mb": size_mb,
                    "query": info.get("query", "")[:100] + "..."  # First 100 chars
                })
                result["total_size_mb"] += size_mb
                result["file_count"] += 1
                
                # Warn about large individual files
                if size_mb > self.size_warning_threshold_mb:
                    logger.warning(
                        f"Cache result file '{result_file.name}' ({size_mb:.1f}MB) "
                        f"exceeds recommended limit ({self.size_warning_threshold_mb}MB)"
                    )
        
        # Add index size to total
        result["total_size_mb"] += result["index_size_mb"]
        
        # Warn about total size
        if result["total_size_mb"] > self.total_size_warning_threshold_mb:
            logger.warning(
                f"Total result cache size ({result['total_size_mb']:.1f}MB) "
                f"exceeds recommended limit ({self.total_size_warning_threshold_mb}MB)"
            )
        
        return result
    
    def clear_cache(self, keep_recent_days: Optional[int] = None):
        """Clear all or old cache entries."""
        if keep_recent_days is None:
            # Clear all
            to_remove = list(self.index.keys())
            logger.info("Clearing entire result cache...")
        else:
            # Clear old entries
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(days=keep_recent_days)
            
            to_remove = []
            for cache_id, info in self.index.items():
                try:
                    timestamp = datetime.fromisoformat(info["timestamp"])
                    if timestamp < cutoff:
                        to_remove.append(cache_id)
                except:
                    pass
            
            logger.info(f"Clearing cache entries older than {keep_recent_days} days...")
        
        # Remove files and index entries
        removed_count = 0
        removed_size_mb = 0.0
        
        for cache_id in to_remove:
            # Handle missing 'file' key
            if "file" not in self.index[cache_id]:
                logger.warning(f"Cache entry {cache_id} missing 'file' key, removing from index")
                del self.index[cache_id]
                removed_count += 1
                continue
                
            result_file = Path(self.index[cache_id]["file"])
            if result_file.exists():
                removed_size_mb += self.get_file_size_mb(result_file)
                result_file.unlink()
                removed_count += 1
            del self.index[cache_id]
        
        self.save_index()
        logger.info(
            f"Cleared {removed_count} cache entries "
            f"({removed_size_mb:.1f}MB freed)"
        )
    
    def clear_old_cache(self, days: int = 7):
        """Clear cache entries older than specified days."""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        
        to_remove = []
        for cache_id, info in self.index.items():
            try:
                timestamp = datetime.fromisoformat(info["timestamp"])
                if timestamp < cutoff:
                    to_remove.append(cache_id)
            except:
                pass
        
        for cache_id in to_remove:
            result_file = Path(self.index[cache_id]["file"])
            if result_file.exists():
                result_file.unlink()
            del self.index[cache_id]
        
        self.save_index()
        logger.info(f"Cleared {len(to_remove)} old cache entries")

# Create singleton instance
result_cache = ResultCacheManager()

def cache_query_result(query: str, result: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Cache a query result and return summary with cache ID."""
    return result_cache.cache_result(query, result)

def get_cached_result(cache_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full cached result by ID."""
    return result_cache.get_cached_result(cache_id)

def estimate_result_tokens(result: Dict[str, Any]) -> int:
    """Estimate token count for a result."""
    return result_cache.estimate_tokens(result)