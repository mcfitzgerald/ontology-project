#!/usr/bin/env python3
"""Test script to validate collaborative flow improvements"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from adk_agents.manufacturing_agent.agent import root_agent
from google.adk.runner import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def test_pareto_flow():
    """Test the Pareto analysis flow to ensure collaborative behavior"""
    
    # Setup
    session_service = InMemorySessionService()
    app_name = "test_collaborative_flow"
    user_id = "test_user"
    session_id = "test_session"
    
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id
    )
    
    runner = Runner(
        agent=root_agent,
        app_name=app_name,
        session_service=session_service
    )
    
    print("=== Testing Collaborative Flow ===\n")
    
    # Test Case 1: Ambiguous analysis request
    print("Test 1: Ambiguous Analysis Request")
    print("User: 'Let's do an analysis of the data'")
    print("Expected: Agent should ask for clarification and offer options\n")
    
    content = types.Content(role='user', parts=[types.Part(text="Let's do an analysis of the data")])
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content
    ):
        if event.is_final_response():
            response = event.content.parts[0].text if event.content and event.content.parts else "No response"
            print(f"Agent: {response}\n")
            
            # Check if agent asked for clarification
            if any(phrase in response.lower() for phrase in ["what would you like", "what type", "which", "clarify", "options"]):
                print("✅ PASS: Agent asked for clarification")
            else:
                print("❌ FAIL: Agent did not ask for clarification")
            break
    
    print("\n" + "="*50 + "\n")
    
    # Test Case 2: Specific request
    print("Test 2: Specific OEE Component Analysis")
    print("User: 'Let's look at OEE components'")
    print("Expected: Agent should proceed with analysis but not dive deep without permission\n")
    
    content = types.Content(role='user', parts=[types.Part(text="Let's look at OEE components")])
    
    found_deep_dive = False
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content
    ):
        if event.is_final_response():
            response = event.content.parts[0].text if event.content and event.content.parts else "No response"
            print(f"Agent: {response[:500]}...")  # Truncate for readability
            
            # Check if agent jumped into deep analysis
            if any(phrase in response.lower() for phrase in ["downtime", "jam", "roi calculation", "annual savings"]):
                found_deep_dive = True
                print("\n❌ FAIL: Agent dove deep without permission")
            elif any(phrase in response.lower() for phrase in ["would you like", "should i", "interested in"]):
                print("\n✅ PASS: Agent offered choices instead of diving deep")
            else:
                print("\n⚠️  UNCLEAR: Check if agent stayed focused on the request")
            break
    
    print("\n" + "="*50 + "\n")
    
    # Test Case 3: Brainstorming request
    print("Test 3: Brainstorming Request")
    print("User: 'How can we look for OEE opportunities?'")
    print("Expected: Agent should offer multiple approaches\n")
    
    content = types.Content(role='user', parts=[types.Part(text="How can we look for OEE opportunities?")])
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content
    ):
        if event.is_final_response():
            response = event.content.parts[0].text if event.content and event.content.parts else "No response"
            print(f"Agent: {response[:500]}...")  # Truncate for readability
            
            # Check if agent offered multiple approaches
            if response.count("•") > 2 or response.count("-") > 2 or response.count("1.") > 0:
                print("\n✅ PASS: Agent offered multiple approaches")
            else:
                print("\n❌ FAIL: Agent did not brainstorm multiple options")
            break
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_pareto_flow())