#!/usr/bin/env python3
"""Direct test of the agent with explicit tool tracking"""
import asyncio
import json
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from adk_agents.manufacturing_agent.agent import root_agent

async def test_agent_direct():
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
        
        # Test with a very explicit query
        query = "Execute this SPARQL query to find equipment: SELECT ?equipment WHERE { ?equipment a ?type . FILTER(?type IN (mes_ontology_populated:Filler, mes_ontology_populated:Packer, mes_ontology_populated:Palletizer)) } LIMIT 10"
        print(f"\nQuery: {query}")
        print("="*80)
        
        user_message = Content(parts=[Part(text=query)])
        
        # Track all events
        all_events = []
        response_text = ""
        
        async for event in runner.run_async(
            user_id="test_user",
            session_id="test_session",
            new_message=user_message
        ):
            # Log event details
            event_data = {
                "type": type(event).__name__,
                "author": getattr(event, 'author', None)
            }
            
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            event_data['text'] = part.text[:100] + "..." if len(part.text) > 100 else part.text
                            response_text += part.text
                            print(part.text, end="", flush=True)
                        
                        if hasattr(part, 'function_call') and part.function_call:
                            event_data['function_call'] = {
                                "name": part.function_call.name,
                                "args": str(part.function_call.args)[:100] + "..."
                            }
                            print(f"\n[TOOL CALL: {part.function_call.name}]", flush=True)
                        
                        if hasattr(part, 'function_response') and part.function_response:
                            event_data['function_response'] = {
                                "name": part.function_response.name,
                                "response": str(part.function_response.response)[:100] + "..."
                            }
                            print(f"\n[TOOL RESPONSE: {part.function_response.name}]", flush=True)
            
            all_events.append(event_data)
        
        print(f"\n\nTotal events: {len(all_events)}")
        print("\nEvent summary:")
        for i, event in enumerate(all_events):
            print(f"{i+1}. {event}")
        
        # Save detailed log
        with open('agent_test_log.json', 'w') as f:
            json.dump({
                "query": query,
                "response": response_text,
                "events": all_events
            }, f, indent=2)
        
    finally:
        # Kill API process
        api_process.terminate()
        api_process.wait()
        print("\nSPARQL API stopped")

if __name__ == "__main__":
    asyncio.run(test_agent_direct())