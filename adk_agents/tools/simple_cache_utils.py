"""Simple cache utility functions for monitoring and management."""
import logging
from adk_agents.tools.cache_manager import cache_manager
from adk_agents.tools.result_cache import result_cache

logger = logging.getLogger(__name__)


def check_all_caches():
    """Check and report on all cache sizes."""
    print("\n=== CACHE STATUS REPORT ===")
    
    # Check main cache
    sizes = cache_manager.check_cache_size()
    total_main = sum(sizes.values())
    
    print(f"\nMain Cache (Total: {total_main:.1f}MB)")
    print(f"  - Query Cache: {sizes['query_cache']:.1f}MB")
    print(f"  - Patterns: {sizes['successful_patterns']:.1f}MB")
    print(f"  - Stats: {sizes['cache_stats']:.1f}MB")
    
    # Check result cache
    result_info = result_cache.check_cache_size()
    
    print(f"\nResult Cache (Total: {result_info['total_size_mb']:.1f}MB)")
    print(f"  - Index: {result_info['index_size_mb']:.1f}MB")
    print(f"  - Files: {result_info['file_count']} cached results")
    
    # Overall status
    grand_total = total_main + result_info['total_size_mb']
    print(f"\nGRAND TOTAL: {grand_total:.1f}MB")
    
    if grand_total > 500:
        print("\n⚠️  WARNING: Total cache size exceeds 500MB!")
        print("   Consider running clear_all_caches() to free up space.")
    elif grand_total > 200:
        print("\n⚠️  NOTICE: Cache is getting large.")
        print("   Consider clearing old entries with clear_old_caches().")
    else:
        print("\n✅ Cache size is within normal limits.")


def clear_all_caches():
    """Clear all caches with confirmation."""
    response = input("\n⚠️  This will delete ALL cached data. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    print("\nClearing caches...")
    
    # Clear main cache
    cache_manager.clear_cache(clear_patterns=True)
    print("✓ Main cache cleared")
    
    # Clear result cache
    result_cache.clear_cache()
    print("✓ Result cache cleared")
    
    print("\n✅ All caches cleared successfully!")
    check_all_caches()


def clear_old_caches(days=7):
    """Clear cache entries older than specified days."""
    print(f"\nClearing cache entries older than {days} days...")
    
    # Clear old results
    result_cache.clear_cache(keep_recent_days=days)
    
    print(f"✅ Old cache entries cleared!")
    check_all_caches()


if __name__ == "__main__":
    # When run directly, show cache status
    check_all_caches()