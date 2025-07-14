#!/usr/bin/env python3
"""
Test script for Vertex AI cost monitoring and token counting.
Demonstrates how to use the SafeVertexAIClient and TokenCounter.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adk_agents.utils import (
    TokenCounter, 
    SafeVertexAIClient, 
    VERTEX_AI_PRICING,
    VERTEX_AI_MONITOR_AVAILABLE
)


def test_token_counting():
    """Test token counting and cost estimation."""
    print("=== Token Counting and Cost Estimation Test ===\n")
    
    if not VERTEX_AI_MONITOR_AVAILABLE:
        print("Note: Vertex AI SDK not available. Using estimation mode.\n")
    
    # Initialize token counter
    counter = TokenCounter("gemini-2.0-flash")
    
    # Test prompts of different sizes
    test_prompts = [
        {
            "name": "Simple Query",
            "prompt": "What is the current OEE for Line 1?",
            "expected_output_ratio": 0.5
        },
        {
            "name": "Analysis Request",
            "prompt": """
            Analyze the manufacturing data for the past week and identify:
            1. Equipment with the lowest OEE
            2. Most common downtime reasons
            3. Quality issues by product type
            4. Opportunities for improvement
            Provide specific recommendations with estimated financial impact.
            """,
            "expected_output_ratio": 2.0
        },
        {
            "name": "Complex Investigation",
            "prompt": """
            I need a comprehensive analysis of our manufacturing performance:
            
            1. Deep dive into micro-stops across all production lines
            2. Correlation analysis between changeover times and product complexity
            3. Quality defect patterns related to specific operators or shifts
            4. Hidden capacity analysis with financial opportunity quantification
            5. Predictive maintenance recommendations based on equipment behavior
            
            For each finding, provide:
            - Root cause analysis
            - Financial impact calculation
            - Specific improvement recommendations
            - Implementation priority and timeline
            
            Focus on opportunities that can deliver >$100k annual savings.
            """,
            "expected_output_ratio": 3.0
        }
    ]
    
    total_estimated_cost = 0
    
    for test in test_prompts:
        print(f"\n{test['name']}:")
        print("-" * 40)
        
        # Count tokens
        token_info = counter.count_tokens(test['prompt'])
        print(f"Input tokens: {token_info['total_tokens']}")
        print(f"Billable characters: {token_info.get('billable_characters', 'N/A')}")
        
        # Estimate cost
        cost_info = counter.estimate_cost(
            test['prompt'], 
            expected_output_ratio=test['expected_output_ratio']
        )
        
        print(f"Expected output tokens: {cost_info['estimated_output_tokens']}")
        print(f"Input cost: ${cost_info['input_cost']:.6f}")
        print(f"Estimated output cost: ${cost_info['estimated_output_cost']:.6f}")
        print(f"Total estimated cost: ${cost_info['estimated_total_cost']:.6f}")
        
        total_estimated_cost += cost_info['estimated_total_cost']
    
    print(f"\n\nTotal estimated cost for all queries: ${total_estimated_cost:.6f}")
    
    # Show pricing reference
    print("\n\n=== Current Model Pricing ===")
    for model, pricing in VERTEX_AI_PRICING.items():
        print(f"\n{model}:")
        print(f"  Input: ${pricing.input_per_million:.2f} per million tokens")
        print(f"  Output: ${pricing.output_per_million:.2f} per million tokens")


def test_safe_client():
    """Test the SafeVertexAIClient with limits."""
    print("\n\n=== Safe Client Test ===\n")
    
    # Create a safe client with conservative limits
    safe_client = SafeVertexAIClient(
        model_name="gemini-2.0-flash",
        daily_request_limit=100,
        daily_cost_limit=1.0,
        hourly_request_limit=20,
        persist_stats=True
    )
    
    # Check current usage
    usage = safe_client.get_usage_summary()
    print("Current Usage Summary:")
    print(f"Daily: {usage['daily']['requests']} requests, ${usage['daily']['cost']:.4f}")
    print(f"Hourly: {usage['hourly']['requests']} requests")
    print(f"Daily limits: {usage['daily']['limit_requests']} requests, ${usage['daily']['limit_cost']}")
    
    # Estimate remaining capacity
    remaining = safe_client.estimate_remaining_requests()
    print(f"\nRemaining capacity:")
    print(f"  By cost: {remaining['by_cost']} requests")
    print(f"  By daily limit: {remaining['by_daily_limit']} requests")
    print(f"  By hourly limit: {remaining['by_hourly_limit']} requests")
    print(f"  Effective: {remaining['effective']} requests")
    
    # Simulate a request (without actually calling Vertex AI)
    print("\n\nSimulating request cost tracking...")
    
    test_prompt = "Analyze equipment efficiency and identify improvement opportunities"
    
    # Pre-flight check
    cost_estimate = safe_client.token_counter.estimate_cost(test_prompt)
    allowed, reason = safe_client._check_limits(cost_estimate['estimated_total_cost'])
    
    if allowed:
        print("✅ Request would be allowed")
        print(f"   Estimated cost: ${cost_estimate['estimated_total_cost']:.6f}")
    else:
        print(f"❌ Request would be blocked: {reason}")
    
    # Show stats file location
    print(f"\n\nUsage stats are persisted to: {safe_client.stats_file}")


def test_cost_benefit_analysis():
    """Demonstrate cost/benefit analysis for manufacturing insights."""
    print("\n\n=== Cost/Benefit Analysis ===\n")
    
    # Example: Calculate ROI for using AI to find opportunities
    
    # Costs
    queries_per_analysis = 10
    cost_per_query = 0.005  # $0.005 average
    total_cost = queries_per_analysis * cost_per_query
    
    # Benefits (example opportunities found)
    opportunities = [
        {"name": "Reduce micro-stops on Line 1", "annual_value": 125000},
        {"name": "Optimize changeover procedures", "annual_value": 85000},
        {"name": "Improve quality controls", "annual_value": 65000},
    ]
    
    total_benefit = sum(opp['annual_value'] for opp in opportunities)
    
    print(f"Analysis cost: ${total_cost:.2f}")
    print(f"Opportunities found: {len(opportunities)}")
    print(f"Total annual benefit: ${total_benefit:,}")
    print(f"ROI ratio: {total_benefit/total_cost:,.0f}x")
    print(f"Payback time: <1 day")
    
    print("\nOpportunities:")
    for opp in opportunities:
        print(f"  - {opp['name']}: ${opp['annual_value']:,}/year")


if __name__ == "__main__":
    # Run all tests
    test_token_counting()
    test_safe_client()
    test_cost_benefit_analysis()
    
    print("\n\n✅ All tests completed!")
    print("\nNote: This is a demonstration of cost monitoring capabilities.")
    print("Actual API calls to Vertex AI were not made in this test.")