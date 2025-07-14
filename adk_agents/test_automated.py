#!/usr/bin/env python3
"""
Automated test script for ADK Manufacturing Analytics Agents.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from adk_agents.agents.orchestrator import create_orchestrator
from adk_agents.agents.explorer_agent import create_explorer_agent
from adk_agents.agents.query_agent import create_query_builder_agent
from adk_agents.agents.analyst_agent import create_analyst_agent
from adk_agents.config.settings import validate_config


async def test_hidden_capacity_analysis():
    """Test the hidden capacity analysis pattern."""
    print("\n=== Testing Hidden Capacity Analysis ===")
    
    # Validate configuration
    validate_config()
    
    # Create agents
    explorer = create_explorer_agent()
    query_builder = create_query_builder_agent()
    analyst = create_analyst_agent()
    
    # Create orchestrator with sub-agents
    orchestrator = create_orchestrator([explorer, query_builder, analyst])
    
    # Create runner
    runner = Runner(
        app_name="ManufacturingAnalytics",
        agent=orchestrator,
        session_service=InMemorySessionService()
    )
    
    # Test query
    query = """Analyze hidden capacity opportunities by identifying equipment 
    with OEE below 85% and calculate the financial impact of improvements."""
    
    print(f"\nQuery: {query}")
    print("\nProcessing...")
    
    try:
        # Execute query
        response = await runner.run(query)
        
        print("\n=== RESPONSE ===")
        print(response)
        
        return True
    except Exception as e:
        print(f"\nError: {e}")
        return False


async def test_temporal_patterns():
    """Test temporal pattern discovery."""
    print("\n=== Testing Temporal Pattern Discovery ===")
    
    validate_config()
    
    # Create agents
    explorer = create_explorer_agent()
    query_builder = create_query_builder_agent()
    analyst = create_analyst_agent()
    orchestrator = create_orchestrator([explorer, query_builder, analyst])
    
    # Create runner
    runner = Runner(
        app_name="ManufacturingAnalytics",
        agent=orchestrator,
        session_service=InMemorySessionService()
    )
    
    query = """Find temporal patterns in equipment downtime events. 
    Look for clustering within 15-minute windows and identify peak problem periods."""
    
    print(f"\nQuery: {query}")
    print("\nProcessing...")
    
    try:
        response = await runner.run(query)
        print("\n=== RESPONSE ===")
        print(response)
        return True
    except Exception as e:
        print(f"\nError: {e}")
        return False


async def test_quality_impact():
    """Test quality impact analysis."""
    print("\n=== Testing Quality Impact Analysis ===")
    
    validate_config()
    
    # Create agents
    explorer = create_explorer_agent()
    query_builder = create_query_builder_agent()
    analyst = create_analyst_agent()
    orchestrator = create_orchestrator([explorer, query_builder, analyst])
    
    # Create runner
    runner = Runner(
        app_name="ManufacturingAnalytics",
        agent=orchestrator,
        session_service=InMemorySessionService()
    )
    
    query = """Analyze the financial impact of quality issues by product type. 
    Calculate scrap costs and identify which products have the highest quality-related losses."""
    
    print(f"\nQuery: {query}")
    print("\nProcessing...")
    
    try:
        response = await runner.run(query)
        print("\n=== RESPONSE ===")
        print(response)
        return True
    except Exception as e:
        print(f"\nError: {e}")
        return False


async def test_sparql_connectivity():
    """Test basic SPARQL connectivity."""
    print("\n=== Testing SPARQL Connectivity ===")
    
    from adk_agents.tools.sparql_tool import execute_sparql_query
    
    # Simple test query
    test_query = """
    SELECT ?s ?p ?o 
    WHERE { 
        ?s ?p ?o 
    } 
    LIMIT 5
    """
    
    try:
        # execute_sparql_query is synchronous, not async
        result = execute_sparql_query(test_query)
        if result.get('status') == 'success':
            print("✅ SPARQL connectivity: OK")
            print(f"   Retrieved {result['data']['row_count']} rows")
            return True
        else:
            print("❌ SPARQL connectivity: FAILED")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ SPARQL connectivity: ERROR - {e}")
        return False


async def main():
    """Run all tests."""
    print("ADK Manufacturing Analytics Agents - Automated Test")
    print("=" * 50)
    
    # Test results
    results = []
    
    # Test SPARQL connectivity first
    results.append(("SPARQL Connectivity", await test_sparql_connectivity()))
    
    # Run analysis tests
    results.append(("Hidden Capacity Analysis", await test_hidden_capacity_analysis()))
    results.append(("Temporal Pattern Discovery", await test_temporal_patterns()))
    results.append(("Quality Impact Analysis", await test_quality_impact()))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! The ADK agents are working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main())