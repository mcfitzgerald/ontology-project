#!/usr/bin/env python3
"""Test agent with very explicit tool use request"""
import asyncio
import json
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from adk_agents.manufacturing_agent.agent import root_agent

async def test_agent_tool_use():
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
        
        # Test queries that should force tool use
        queries = [
            "Find equipment with OEE below 85% and calculate the improvement opportunity",
            "Show me all Fillers in the ontology",
            "What's the average OEE across all equipment?"
        ]
        
        for query in queries:
            print(f"\n{'='*80}")
            print(f"Query: {query}")
            print('='*80)
            
            user_message = Content(parts=[Part(text=query)])
            
            # Track events
            tool_calls = []
            response_text = ""
            
            async for event in runner.run_async(
                user_id="test_user",
                session_id=f"test_session_{queries.index(query)}",
                new_message=user_message
            ):
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text += part.text
                                print(part.text, end="", flush=True)
                            
                            if hasattr(part, 'function_call') and part.function_call:
                                tool_calls.append({
                                    "name": part.function_call.name,
                                    "args": str(part.function_call.args)[:100]
                                })
                                print(f"\n[TOOL CALL: {part.function_call.name}]", flush=True)
            
            print(f"\n\nTool calls for this query: {len(tool_calls)}")
            if tool_calls:
                for tc in tool_calls:
                    print(f"  - {tc['name']}: {tc['args']}...")
        
    finally:
        # Kill API process
        api_process.terminate()
        api_process.wait()
        print("\nSPARQL API stopped")

if __name__ == "__main__":
    asyncio.run(test_agent_tool_use())