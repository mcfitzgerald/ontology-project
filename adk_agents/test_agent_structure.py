"""Test the agent structure and tools without running API calls."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adk_agents.manufacturing_agent.agent import root_agent

def test_agent_structure():
    """Verify the agent structure and tools are properly configured."""
    
    print("=" * 80)
    print("AGENT STRUCTURE TEST")
    print("=" * 80)
    
    # Check agent configuration
    print(f"\nAgent Name: {root_agent.name}")
    print(f"Agent Description: {root_agent.description}")
    print(f"Output Key: {root_agent.output_key}")
    
    # Check tools
    print(f"\nTools Available: {len(root_agent.tools)}")
    for i, tool in enumerate(root_agent.tools, 1):
        tool_name = tool.function.__name__ if hasattr(tool, 'function') else str(tool)
        print(f"  {i}. {tool_name}")
    
    # Check instruction
    print("\nInstruction Preview:")
    print("-" * 40)
    print(root_agent.instruction[:500] + "...")
    
    # Verify discovery methodology is in instruction
    discovery_keywords = ["EXPLORE", "DISCOVER", "QUANTIFY", "RECOMMEND", "curiosity", "pattern", "hypothesis"]
    found_keywords = [kw for kw in discovery_keywords if kw in root_agent.instruction]
    print(f"\nDiscovery Keywords Found: {len(found_keywords)}/{len(discovery_keywords)}")
    print(f"Keywords: {', '.join(found_keywords)}")
    
    # Check if tools have proper signatures
    print("\nTool Signatures:")
    print("-" * 40)
    
    critical_tools = ["execute_sparql_query", "get_discovery_pattern", "format_insight"]
    for tool_name in critical_tools:
        tool_found = False
        for tool in root_agent.tools:
            if hasattr(tool, 'function') and tool.function.__name__ == tool_name:
                tool_found = True
                func = tool.function
                print(f"{tool_name}: ✓")
                
                # Check if it has the right parameters
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                print(f"  Parameters: {', '.join(params)}")
                
                # Special checks
                if tool_name == "execute_sparql_query" and "hypothesis" in params:
                    print("  ✓ Has hypothesis parameter for discovery tracking")
                if "tool_context" in params:
                    print("  ✓ Has tool_context for state management")
                break
        
        if not tool_found:
            print(f"{tool_name}: ✗ NOT FOUND")
    
    print("\n" + "=" * 80)
    print("STRUCTURE TEST COMPLETE")
    print("=" * 80)
    
    # Summary
    print("\nSummary:")
    print(f"- Agent properly configured: {'✓' if root_agent.name == 'discovery_analyst' else '✗'}")
    print(f"- Discovery methodology present: {'✓' if len(found_keywords) >= 5 else '✗'}")
    print(f"- All tools available: {'✓' if len(root_agent.tools) >= 9 else '✗'}")
    print(f"- State tracking enabled: {'✓' if root_agent.output_key else '✗'}")
    
    return True

if __name__ == "__main__":
    test_agent_structure()