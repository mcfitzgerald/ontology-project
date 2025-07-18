#!/usr/bin/env python3
"""
Example of running ADK agents using the 2025 patterns.

In ADK 2025, you have several options:

1. Use ADK CLI:
   - `adk web` - Starts a web interface
   - `adk run adk_agents` - Runs in CLI mode
   
2. Direct agent interaction (shown below)

3. FastAPI integration for production
"""

import asyncio
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the root agent
from adk_agents import root_agent

# For direct interaction, we can use the agent's methods
# Note: This is for testing/development. Production should use ADK CLI

async def run_example():
    """
    Example of direct agent interaction.
    
    In production, use:
    - `adk web` for interactive web UI
    - `adk run` for CLI interface
    - FastAPI integration for API endpoints
    """
    print("=== ADK 2025 Agent Example ===\n")
    
    # Example queries
    queries = [
        "What equipment has the lowest OEE score?",
        "Show me equipment with high defect rates",
        "What are the main bottlenecks in production?"
    ]
    
    print("Note: This is a demonstration of direct agent usage.")
    print("For production, use 'adk web' or 'adk run' commands.\n")
    
    # The actual implementation would depend on the agent's interface
    # In ADK 2025, agents are typically accessed through the framework
    print("Example queries that can be run through ADK web interface:")
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")
    
    print("\nTo start the ADK web interface:")
    print("  cd to project root and run: adk web adk_agents")
    print("\nTo run in CLI mode:")
    print("  cd to project root and run: adk run adk_agents")


if __name__ == "__main__":
    asyncio.run(run_example())