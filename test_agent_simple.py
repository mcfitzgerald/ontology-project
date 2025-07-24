#!/usr/bin/env python3
"""Simple test of the manufacturing agent"""
import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from adk_agents.manufacturing_agent.agent import root_agent

async def test_agent():
    # First start SPARQL API
    import subprocess
    import time
    
    print("Starting SPARQL API...")
    api_process = subprocess.Popen(
        ["python", "-m", "uvicorn", "API.main:app", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for API to start
    time.sleep(5)
    
    try:
        # Create session service and runner
        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="test_app",
            session_service=session_service
        )
        
        # Create session
        session = await session_service.create_session(
            app_name="test_app",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Test query
        query = "Show me equipment with OEE below 85% and calculate the improvement opportunity"
        print(f"\nQuery: {query}")
        print("="*80)
        
        user_message = Content(parts=[Part(text=query)])
        
        # Run agent
        response_text = ""
        tool_calls = []
        
        async for event in runner.run_async(
            user_id="test_user",
            session_id="test_session",
            new_message=user_message
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text
                        print(part.text, end="", flush=True)
            
            # Track tool calls
            if hasattr(event, 'author') and event.author == 'FunctionCallingAgent':
                if hasattr(event, 'content') and event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'function_call'):
                            tool_calls.append(part.function_call.name)
                            print(f"\n[Tool Call: {part.function_call.name}]", flush=True)
        
        print(f"\n\nTotal tool calls: {len(tool_calls)}")
        print(f"Tools used: {tool_calls}")
        
    finally:
        # Kill API process
        api_process.terminate()
        api_process.wait()
        print("\nSPARQL API stopped")

if __name__ == "__main__":
    asyncio.run(test_agent())