#!/usr/bin/env python3
"""Test the manufacturing agent directly to debug behavior"""
import asyncio
from google.adk.runners import InMemoryRunner
from google.genai import types
from manufacturing_agent import agent as manufacturing_agent

async def test_agent():
    """Test the agent with a simple query"""
    
    # Create runner
    runner = InMemoryRunner(
        agent=manufacturing_agent,
        app_name="test_app"
    )
    
    # Create session
    session_service = runner.session_service
    await session_service.create_session(
        app_name="test_app",
        user_id="test_user",
        session_id="test_session"
    )
    
    # Test query
    test_query = "Show me equipment with OEE below 85%"
    print(f"User Query: {test_query}")
    print("-" * 80)
    
    # Run agent
    async for event in runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=types.Content(
            role="user",
            parts=[types.Part(text=test_query)]
        )
    ):
        if event.is_final_response():
            print("Agent Response:")
            print(event.content.parts[0].text)
            break
        elif hasattr(event, 'type') and event.type == 'tool_call':
            print(f"Tool Call: {event.tool_name}")
            if hasattr(event, 'args'):
                print(f"  Args: {event.args}")

if __name__ == "__main__":
    asyncio.run(test_agent())