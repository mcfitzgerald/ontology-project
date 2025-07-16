"""Test importing the enhanced modules"""
import sys
sys.path.insert(0, '/Users/michael/github/ontology-project')

try:
    print("Testing imports...")
    
    # Test context import
    from adk_agents.context.shared_context import SharedAgentContext
    print("✓ SharedAgentContext imported successfully")
    
    # Test query builder import
    from adk_agents.tools.sparql_builder import SPARQLQueryBuilder
    print("✓ SPARQLQueryBuilder imported successfully")
    
    # Test validator import
    from adk_agents.tools.sparql_validator import validate_and_optimize_query
    print("✓ validate_and_optimize_query imported successfully")
    
    # Test creating instances
    context = SharedAgentContext()
    print("✓ SharedAgentContext instance created")
    
    builder = SPARQLQueryBuilder()
    print("✓ SPARQLQueryBuilder instance created")
    
    # Test basic functionality
    query = builder.build_downtime_pareto_query()
    print("✓ Generated downtime pareto query")
    
    optimized = validate_and_optimize_query(query)
    print("✓ Query validation working")
    
    print("\nAll imports and basic functionality working!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()