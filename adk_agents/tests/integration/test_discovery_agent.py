"""Test the discovery agent with queries from the manual prototype."""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

# Import our agent
from adk_agents.manufacturing_agent.agent import root_agent

async def test_discovery_agent():
    """Test the agent with business questions from the manual prototype."""
    
    # Create session service and runner
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="discovery_test",
        session_service=session_service
    )
    
    # Create a session
    user_id = "test_user"
    session_id = "test_session"
    session = await session_service.create_session(
        app_name="discovery_test",
        user_id=user_id,
        session_id=session_id
    )
    
    print("=" * 80)
    print("TESTING DISCOVERY AGENT WITH MANUAL PROTOTYPE QUERIES")
    print("=" * 80)
    
    # Test queries from the manual prototype
    test_queries = [
        # 1. Initial downtime analysis query
        "Analyze downtime trends across production lines to find optimization opportunities",
        
        # 2. Hidden capacity analysis
        "What's the hidden production capacity if we solve our biggest OEE bottlenecks?",
        
        # 3. Product-specific OEE analysis  
        "Which products are killing our OEE and why? Focus on financial impact.",
        
        # 4. Micro-stop pattern recognition
        "When and why do micro-stops cluster, and what's the cascade effect?",
        
        # 5. Quality-cost trade-off
        "Where are we losing money to scrap, and is it worth fixing?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}: {query}")
        print(f"{'='*80}\n")
        
        # Create user message
        user_message = Content(parts=[Part(text=query)])
        
        # Run the agent
        response_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text
                        print(part.text, end="", flush=True)
        
        print("\n")
        
        # Check session state after each query
        updated_session = await session_service.get_session(
            app_name="discovery_test",
            user_id=user_id,
            session_id=session_id
        )
        
        print("\n--- Session State Summary ---")
        state = updated_session.state
        print(f"Discoveries tracked: {len(state.get('discoveries', []))}")
        print(f"Patterns used: {state.get('patterns_used', [])}")
        print(f"Total value found: ${state.get('total_value_found', 0):,.0f}")
        print(f"Latest discovery saved: {'Yes' if state.get('latest_discovery') else 'No'}")
        
        # Brief pause between queries
        await asyncio.sleep(2)
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL DISCOVERY SUMMARY")
    print("="*80)
    
    final_state = updated_session.state
    print(f"\nTotal discoveries: {len(final_state.get('discoveries', []))}")
    print(f"Failed patterns encountered: {len(final_state.get('failed_patterns', []))}")
    print(f"Total opportunity value: ${final_state.get('total_value_found', 0):,.0f}")
    
    if final_state.get('formatted_insights'):
        print(f"\nFormatted insights: {len(final_state['formatted_insights'])}")
        for insight in final_state['formatted_insights'][:3]:  # Show first 3
            print(f"  - {insight['insight']}")
            print(f"    Impact: {insight['annual_impact']}, Priority: {insight['priority']}")
    
    print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_discovery_agent())