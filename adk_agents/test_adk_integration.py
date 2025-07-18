"""
Test the full ADK integration.
"""
import asyncio
from google.genai.types import Content, Part
from adk_agents.app import runner, session_service, ontology_knowledge

async def test_integration():
    """Test key integration points."""
    
    print("Testing ADK Integration...")
    
    # Test 1: Ontology Knowledge
    print("\n1. Testing Ontology Knowledge:")
    test_questions = [
        "What equipment types are available?",
        "What is OEE?",
        "What properties does Equipment have?"
    ]
    
    for question in test_questions:
        can_answer, answer = ontology_knowledge.can_answer_without_query(question)
        print(f"   Q: {question}")
        print(f"   Can answer: {can_answer}")
        if can_answer:
            print(f"   Answer: {list(answer.keys()) if isinstance(answer, dict) else answer}")
    
    # Test 2: Runner with State
    print("\n2. Testing Runner with State Management:")
    session = await session_service.create_session(
        app_name="mes_ontology_analysis",
        user_id="test_user"
    )
    
    # Ask a schema question (should not trigger SPARQL)
    response_events = []
    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=Content(parts=[Part(text="What equipment types exist?")])
    ):
        response_events.append(event)
    
    print(f"   Events generated: {len(response_events)}")
    print(f"   State changes: {any(e.actions and e.actions.state_delta for e in response_events)}")
    
    # Test 3: Artifact Storage
    print("\n3. Testing Artifact Storage:")
    # This will be tested when a large result is generated
    
    print("\n✅ Integration test complete!")

if __name__ == "__main__":
    asyncio.run(test_integration())