"""Check if the evaluation system can work with our refactored agent."""
import os
import sys
from pathlib import Path

# Set a dummy API key for testing (won't make actual calls)
os.environ["GOOGLE_API_KEY"] = "test_key_for_structure_validation"

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test imports
try:
    from adk_agents.manufacturing_agent import agent
    print("✓ Agent module imported successfully")
    print(f"  Agent name: {agent.name}")
    print(f"  Agent tools: {len(agent.tools)}")
except Exception as e:
    print(f"✗ Failed to import agent: {e}")
    sys.exit(1)

try:
    from google.adk.evaluation.agent_evaluator import AgentEvaluator
    print("\n✓ ADK evaluator imported successfully")
except Exception as e:
    print(f"\n✗ Failed to import evaluator: {e}")
    sys.exit(1)

# Check evalset files
evalset_dir = Path("evaluation/evalsets")
if evalset_dir.exists():
    evalsets = list(evalset_dir.glob("*.evalset.json"))
    print(f"\n✓ Found {len(evalsets)} evaluation sets:")
    for evalset in evalsets:
        print(f"  - {evalset.name}")
else:
    print("\n✗ Evalset directory not found")

# Check if we can access the agent's tools
print("\n✓ Agent tools accessible:")
for i, tool in enumerate(agent.tools[:5], 1):  # Show first 5
    try:
        # Try to get function name from FunctionTool
        if hasattr(tool, '_function'):
            name = tool._function.__name__
        elif hasattr(tool, 'function'):
            name = tool.function.__name__
        else:
            name = str(type(tool).__name__)
        print(f"  {i}. {name}")
    except:
        print(f"  {i}. {type(tool).__name__}")

print("\n✓ Evaluation system appears ready!")
print("\nTo run evaluations:")
print("  1. Set GOOGLE_API_KEY environment variable")
print("  2. Run: adk eval manufacturing_agent evaluation/evalsets/discovery_first.evalset.json")
print("  3. Or use: python -m pytest evaluation/test_agent_evaluation.py -v")