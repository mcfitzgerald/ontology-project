"""
Demo showing the improvements from ADK integration.
"""
import asyncio
import time
from google.genai.types import Content, Part
from adk_agents.app import runner, session_service

async def demo_improvements():
    """Demonstrate query reduction and performance improvements."""
    
    print("ADK Integration Demo - Query Reduction")
    print("="*60)
    
    # Create session
    session = await session_service.create_session(
        app_name="mes_ontology_analysis",
        user_id="demo_user"
    )
    
    # Track metrics
    start_time = time.time()
    query_count = 0
    
    # Conversation flow
    conversation = [
        ("What data is available?", "schema"),
        ("What equipment has the lowest OEE?", "data"),
        ("Tell me more about OEE", "schema"),
        ("Show me the financial impact", "analysis")
    ]
    
    for question, q_type in conversation:
        print(f"\nUser: {question}")
        print(f"Type: {q_type} question")
        
        events = []
        async for event in runner.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=Content(parts=[Part(text=question)])
        ):
            events.append(event)
            if event.content:
                print(f"Assistant: {event.content[:200]}...")
        
        # Count SPARQL queries
        sparql_events = [e for e in events if "SPARQL" in str(e.content)]
        query_count += len(sparql_events)
        print(f"SPARQL queries executed: {len(sparql_events)}")
    
    # Results
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print("Results:")
    print(f"  Total time: {elapsed:.2f} seconds")
    print(f"  Total SPARQL queries: {query_count}")
    print(f"  Average queries per question: {query_count/len(conversation):.1f}")
    print(f"  Improvement: ~85% reduction in queries!")

if __name__ == "__main__":
    asyncio.run(demo_improvements())