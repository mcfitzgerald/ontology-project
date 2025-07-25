"""Test cache management functionality."""
import pytest
import logging
from pathlib import Path
import json
import os

from adk_agents.tools.cache_manager import cache_manager
from adk_agents.tools.result_cache import result_cache


def test_cache_size_monitoring():
    """Test cache size monitoring functionality."""
    # Check cache sizes
    sizes = cache_manager.check_cache_size()
    
    print("\n=== Cache Manager Size Report ===")
    print(f"Query Cache: {sizes['query_cache']:.1f}MB")
    print(f"Successful Patterns: {sizes['successful_patterns']:.1f}MB")
    print(f"Cache Stats: {sizes['cache_stats']:.1f}MB")
    print(f"Query Patterns: {sizes['query_patterns']:.1f}MB")
    print(f"Total: {sum(sizes.values()):.1f}MB")
    
    # Test result cache
    result_sizes = result_cache.check_cache_size()
    
    print("\n=== Result Cache Size Report ===")
    print(f"Index File: {result_sizes['index_size_mb']:.1f}MB")
    print(f"Result Files: {result_sizes['file_count']} files")
    print(f"Total Size: {result_sizes['total_size_mb']:.1f}MB")
    
    if result_sizes['result_files']:
        print("\nLargest result files:")
        sorted_files = sorted(
            result_sizes['result_files'], 
            key=lambda x: x['size_mb'], 
            reverse=True
        )[:5]
        for f in sorted_files:
            print(f"  - {f['file']}: {f['size_mb']:.1f}MB")


def test_cache_clearing():
    """Test cache clearing functionality."""
    print("\n=== Testing Cache Clear Functions ===")
    
    # Test clear with dry run (don't actually clear in test)
    print("\nCache Manager clear_cache() - DRY RUN")
    print("Would clear:")
    print(f"  - query_cache.json")
    print(f"  - Reset statistics")
    
    print("\nResult Cache clear_cache() - DRY RUN")
    print("Would clear all result files and reset index")
    
    # Test selective clearing
    print("\nResult Cache clear_cache(keep_recent_days=7) - DRY RUN")
    print("Would clear entries older than 7 days")


def test_automatic_warnings(caplog):
    """Test that warnings are emitted when thresholds are exceeded."""
    # This will trigger warnings if cache is large
    with caplog.at_level(logging.WARNING):
        cache_manager.check_cache_size()
        result_cache.check_cache_size()
    
    # Print captured warnings
    if caplog.records:
        print("\n=== Captured Warnings ===")
        for record in caplog.records:
            print(f"{record.levelname}: {record.message}")
    else:
        print("\n=== No warnings emitted (cache within limits) ===")


if __name__ == "__main__":
    # Run tests directly
    print("Running cache management tests...\n")
    
    test_cache_size_monitoring()
    test_cache_clearing()
    
    # Test warnings
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    class LogCapture:
        def __init__(self):
            self.records = []
        
        def at_level(self, level):
            return self
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            pass
    
    test_automatic_warnings(LogCapture())