"""
Example script showing how to use the ADK runner for analysis.
"""
import asyncio
from google.genai.types import Content, Part
from adk_agents.app import runner, session_service

async def run_analysis():
    """Run example analysis queries using ADK runner."""
    
    # Create a session
    session = await session_service.create_session(
        app_name="mes_ontology_analysis",
        user_id="analyst_1",
        state={
            "user:preferred_format": "detailed",
            "analysis_focus": "efficiency_optimization"
        }
    )
    
    print(f"Created session: {session.id}")
    print(f"Initial state: {session.state}")
    
    # Example queries demonstrating the system
    queries = [
        # Schema questions (answered from cache)
        "What types of equipment are available in the factory?",
        "What metrics can I analyze?",
        
        # Data questions (require SPARQL)
        "Show me equipment with OEE below 80%",
        "What are the main bottlenecks in production?",
        "Calculate the financial impact of improving OEE by 10%"
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        # Run the query through ADK runner
        async for event in runner.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=Content(parts=[Part(text=query)])
        ):
            # Process events
            if event.content:
                print(f"\nAgent: {event.content}")
            
            # Show state changes
            if event.actions and event.actions.state_delta:
                print(f"\nState updated: {event.actions.state_delta}")
    
    # Show final session state
    final_session = await session_service.get_session(
        app_name="mes_ontology_analysis",
        user_id=session.user_id,
        session_id=session.id
    )
    print(f"\n{'='*60}")
    print("Final session state:")
    for key, value in final_session.state.items():
        if not key.startswith("temp:"):
            print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(run_analysis())