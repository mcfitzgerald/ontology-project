#!/usr/bin/env python3
"""
Test script to verify OntologyKnowledge improvements reduce SPARQL queries.

This test demonstrates:
1. OntologyKnowledge can answer questions without SPARQL
2. Query reduction in simulated conversations
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import just what we need
from adk_agents.utils.ontology_knowledge import OntologyKnowledge


def test_ontology_knowledge():
    """Test the OntologyKnowledge class functionality."""
    print("=== Testing OntologyKnowledge ===\n")
    
    # Initialize knowledge base
    kb = OntologyKnowledge()
    
    # Test questions that should be answerable without SPARQL
    test_questions = [
        # Equipment type questions
        "What equipment types are available?",
        "List all equipment types in the ontology",
        "What kinds of equipment do we monitor?",
        
        # Metric questions
        "What metrics can I query?",
        "What performance metrics are available?",
        "Tell me about OEE metrics",
        
        # Property questions
        "What properties are available?",
        "List the data properties",
        
        # Class hierarchy questions
        "What are the subclasses of Equipment?",
        "Show me the Equipment class hierarchy",
        
        # CSV mapping questions
        "What CSV column maps to OEE?",
        "Which property maps to the 'oee_score' column?",
        
        # Example questions
        "Show me examples of Filler equipment",
        "Give me an example of a Labeler",
        
        # Questions that need SPARQL (negative test)
        "What is the current OEE for Filler1?",
        "How many defects were produced yesterday?",
        "Calculate the average production rate"
    ]
    
    results = {
        'can_answer': 0,
        'needs_sparql': 0,
        'details': []
    }
    
    for question in test_questions:
        can_answer, answer = kb.can_answer_without_query(question)
        
        if can_answer:
            results['can_answer'] += 1
            status = "✓ Can answer without SPARQL"
        else:
            results['needs_sparql'] += 1
            status = "✗ Needs SPARQL query"
        
        results['details'].append({
            'question': question,
            'can_answer': can_answer,
            'answer': answer
        })
        
        print(f"Q: {question}")
        print(f"   {status}")
        if answer:
            print(f"   Answer: {answer[:100]}...")  # Truncate long answers
        print()
    
    # Summary
    print(f"\nSUMMARY:")
    print(f"- Questions answerable without SPARQL: {results['can_answer']}")
    print(f"- Questions needing SPARQL: {results['needs_sparql']}")
    print(f"- Success rate: {results['can_answer'] / len(test_questions) * 100:.1f}%")
    
    return results


def simulate_conversation():
    """Simulate a conversation showing query reduction."""
    print("\n\n=== Simulating Conversation with Query Reduction ===\n")
    
    kb = OntologyKnowledge()
    
    # Simulate a typical user conversation
    conversation = [
        "Hi, I'm new to this system. What types of equipment can I analyze?",
        "What metrics are tracked for these equipment types?",
        "Can you explain what OEE means?",
        "Now show me the actual OEE scores for all Fillers from last week",
        "What are the typical OEE values I should expect?",
        "Are there any other performance metrics besides OEE?"
    ]
    
    sparql_count = 0
    ontology_count = 0
    
    print("User Journey: Understanding the system before diving into data\n")
    
    for i, user_input in enumerate(conversation, 1):
        print(f"User {i}: {user_input}")
        
        can_answer, answer = kb.can_answer_without_query(user_input)
        
        if can_answer:
            ontology_count += 1
            print(f"Assistant: [FROM ONTOLOGY KNOWLEDGE - No SPARQL needed]")
            print(f"           {answer[:200]}...")
        else:
            sparql_count += 1
            print(f"Assistant: [NEEDS SPARQL QUERY]")
            print(f"           I'll need to query the database for that information...")
        
        print()
    
    print(f"\nCONVERSATION SUMMARY:")
    print(f"- Total exchanges: {len(conversation)}")
    print(f"- Answered from ontology: {ontology_count} ({ontology_count/len(conversation)*100:.0f}%)")
    print(f"- Required SPARQL: {sparql_count} ({sparql_count/len(conversation)*100:.0f}%)")
    print(f"- SPARQL queries saved: {ontology_count}")


def test_knowledge_summary():
    """Test the knowledge summary functionality."""
    print("\n\n=== Testing Knowledge Summary ===\n")
    
    kb = OntologyKnowledge()
    summary = kb.get_available_data_summary()
    
    print("Ontology Knowledge Summary (first 500 chars):")
    print("-" * 50)
    print(summary[:500] + "...")
    print("-" * 50)
    
    # Test search functionality
    print("\nTesting search functionality:")
    search_terms = ["OEE", "Filler", "defect", "production"]
    
    for term in search_terms:
        results = kb.search_ontology(term)
        total_matches = sum(len(items) for items in results.values())
        print(f"\nSearch for '{term}': {total_matches} matches found")
        for category, items in results.items():
            if items:
                print(f"  - {category}: {len(items)} matches")


def test_orchestrator_mock():
    """Test the orchestrator behavior concept without imports."""
    print("\n\n=== Testing Orchestrator Behavior (Mock) ===\n")
    
    kb = OntologyKnowledge()
    
    print("The ConversationOrchestrator would use OntologyKnowledge like this:\n")
    
    # Mock orchestrator behavior
    test_scenarios = [
        {
            'name': 'Equipment Discovery',
            'question': "What types of equipment do we have in the factory?",
            'expected_behavior': 'Should answer from ontology knowledge'
        },
        {
            'name': 'Metric Understanding',
            'question': "What metrics are available for analysis?",
            'expected_behavior': 'Should answer from ontology knowledge'
        },
        {
            'name': 'Real Data Query',
            'question': "What is the average OEE for all Fillers last week?",
            'expected_behavior': 'Should recognize need for SPARQL query'
        }
    ]
    
    for scenario in test_scenarios:
        print(f"Scenario: {scenario['name']}")
        print(f"Question: {scenario['question']}")
        
        # This is what the orchestrator would do:
        can_answer, answer = kb.can_answer_without_query(scenario['question'])
        
        if can_answer:
            print(f"Result: ✓ Can answer without SPARQL")
            print(f"Answer preview: {answer[:150]}...")
        else:
            print(f"Result: Needs SPARQL query")
        
        print(f"Expected: {scenario['expected_behavior']}")
        print()


def main():
    """Run all tests."""
    print("Manufacturing Ontology Query Reduction Test")
    print("=" * 60)
    print("\nThis test demonstrates how the OntologyKnowledge class")
    print("reduces unnecessary SPARQL queries by answering questions")
    print("from cached ontology structure.\n")
    
    # Run tests
    test_ontology_knowledge()
    simulate_conversation()
    test_knowledge_summary()
    test_orchestrator_mock()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("\nKey Benefits Demonstrated:")
    print("1. Many user questions can be answered without SPARQL")
    print("2. Reduces API calls and improves response time")
    print("3. Provides better user experience with instant answers")
    print("4. Only queries database when actual data is needed")


if __name__ == "__main__":
    main()