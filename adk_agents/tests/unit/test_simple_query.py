#!/usr/bin/env python3
"""Simple test to verify agent can execute basic queries."""

import asyncio
from google.adk.runners import LocalRunner
from manufacturing_agent.agent import root_agent

async def test_agent():
    """Test the agent with a simple query."""
    runner = LocalRunner(root_agent)
    
    # Test query
    query = "What equipment exists in the system?"
    
    print(f"Testing agent with query: {query}")
    print("-" * 50)
    
    try:
        async for event in runner.run_async(query):
            if event.response:
                print(f"Agent response: {event.response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent())