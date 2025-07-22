#!/usr/bin/env python3
"""Direct test of the manufacturing agent."""

import asyncio
from manufacturing_agent import agent
from google.adk.invocations import AsyncInvocation

async def test_agent():
    """Test the agent with a simple query."""
    # Create an invocation
    invocation = AsyncInvocation(
        agent=agent,
        user_msg="Find equipment with significant capacity improvement opportunities"
    )
    
    # Run the invocation
    result = await invocation.execute()
    
    print("Agent Response:")
    print("=" * 80)
    if result.final_response:
        print(result.final_response.parts[0].text)
    else:
        print("No final response received")
        
    print("\nTool Uses:")
    print("=" * 80)
    for tool_use in result.intermediate_data.tool_uses:
        print(f"Tool: {tool_use.name}")
        print(f"Args: {tool_use.args}")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(test_agent())