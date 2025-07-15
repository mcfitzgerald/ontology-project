"""Test the enhanced ADK agents"""
import asyncio
from tools.sparql_tool import query_downtime_pareto, query_oee_analysis
from context.shared_context import SharedAgentContext

async def test_enhanced_features():
    """Test the new query builder and context features"""
    print("Testing Enhanced ADK Agent Features")
    print("=" * 50)
    
    # Test 1: Query Builder with aggregation
    print("\n1. Testing Downtime Pareto Query:")
    result = await query_downtime_pareto()
    if result['success']:
        print(f"✓ Query successful! Found {result['row_count']} downtime reasons")
    else:
        print(f"✗ Query failed: {result['error']}")
        if result.get('suggestions'):
            print(f"  Suggestions: {result['suggestions']}")
    
    # Test 2: OEE Analysis Query
    print("\n2. Testing OEE Analysis Query:")
    result = await query_oee_analysis()
    if result['success']:
        print(f"✓ Query successful! Found {result['row_count']} equipment OEE records")
    else:
        print(f"✗ Query failed: {result['error']}")
    
    # Test 3: Shared Context
    print("\n3. Testing Shared Context:")
    context = SharedAgentContext()
    
    # Simulate caching some discoveries
    context.cache_property_discovery("Equipment", [
        {"property": "hasEquipmentID", "type": "literal"},
        {"property": "belongsToLine", "type": "iri"}
    ])
    
    # Check if caching works
    cached = context.get_cached_properties("Equipment")
    if cached:
        print(f"✓ Context caching works! Found {len(cached['properties'])} properties")
    else:
        print("✗ Context caching failed")
    
    # Test known issues recording
    context.record_known_issue(
        "timestamp_filtering",
        "Timestamps are literals not IRIs",
        "Remove FILTER(ISIRI(?timestamp))"
    )
    
    print(f"✓ Recorded {len(context.known_issues)} known issues")
    
    # Summary
    print("\n" + context.get_summary())

if __name__ == "__main__":
    asyncio.run(test_enhanced_features())