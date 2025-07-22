#!/usr/bin/env python3
"""
Interactive testing of the discovery agent.
This shows how the agent performs without strict evaluation constraints.
"""
import asyncio
import os
from google.adk import InvocationContext
from manufacturing_agent.agent import root_agent

async def test_discovery():
    """Test the agent with manual prototype queries."""
    
    # Test queries from manual prototype
    queries = [
        "Find equipment with significant capacity improvement opportunities",
        "Analyze downtime patterns and find any clustering or shift-based trends",
        "Where can we reduce scrap costs and improve quality?",
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        # Create invocation context
        ctx = InvocationContext(
            user_message=query,
            session_id="test_session",
            user_id="test_user"
        )
        
        # Run agent
        response = None
        tool_count = 0
        
        async for event in root_agent.run_async(ctx):
            if hasattr(event, 'tool_use'):
                tool_count += 1
                print(f"🔧 Tool {tool_count}: {event.tool_use.name}")
                if event.tool_use.name == 'format_insight':
                    # Show the discovered insight
                    args = event.tool_use.args
                    print(f"\n💡 DISCOVERY:")
                    print(f"   Finding: {args.get('finding', 'N/A')}")
                    print(f"   Impact: ${args.get('impact', 0):,.0f}")
                    print(f"   Action: {args.get('action', 'N/A')}")
                    
            elif hasattr(event, 'response'):
                response = event.response
        
        if response:
            print(f"\n📊 FINAL RESPONSE:")
            print(response)

if __name__ == "__main__":
    # Set up environment
    os.environ['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY', '')
    
    print("🚀 Starting Interactive Agent Test")
    print("This shows how the agent discovers insights without evaluation constraints")
    
    asyncio.run(test_discovery())