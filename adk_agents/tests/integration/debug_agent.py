#!/usr/bin/env python3
"""Debug the agent's response to capacity query."""

import asyncio
from manufacturing_agent import agent
from google.genai import types
from google.adk.agents.models import AsyncInvocation

async def test_capacity_query():
    """Test the agent with capacity improvement query."""
    # Create user message
    user_msg = types.Content(
        role="user",
        parts=[types.Part(text="Find equipment with significant capacity improvement opportunities")]
    )
    
    # Create invocation
    invocation = AsyncInvocation(
        agent=agent,
        user_content=user_msg
    )
    
    # Process and collect results
    print("Sending query to agent...")
    print("-" * 80)
    
    result = await invocation.execute()
    
    # Print final response
    if result.final_response:
        print("\nFinal Response:")
        print("=" * 80)
        for part in result.final_response.parts:
            if part.text:
                print(part.text)
    else:
        print("\nNo final response received!")
        
    # Print tool uses
    print("\n\nTool Uses:")
    print("=" * 80)
    if result.intermediate_data and result.intermediate_data.tool_uses:
        for i, tool_use in enumerate(result.intermediate_data.tool_uses):
            print(f"\n{i+1}. Tool: {tool_use.name}")
            print(f"   Args: {tool_use.args}")
    else:
        print("No tools used!")
        
    return result

if __name__ == "__main__":
    asyncio.run(test_capacity_query())