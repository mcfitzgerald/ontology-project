"""
Run evaluation using flexible validators instead of strict trajectory matching.
"""
import json
from flexible_validators import validate_target_based_response

# Load the actual agent results
with open('../manufacturing_agent/.adk/eval_history/manufacturing_agent_manual_prototype_targets_1753143002.4005492.evalset_result.json', 'r') as f:
    data = json.loads(json.loads(f.read()))

# Evaluate each test case with flexible validation
for test_case in data['eval_case_results']:
    actual = test_case['eval_metric_result_per_invocation'][0]['actual_invocation']
    
    # Extract response and tool uses
    response_text = actual['final_response']['parts'][0]['text'] if actual.get('final_response') else ""
    tool_uses = actual['intermediate_data']['tool_uses']
    
    # Define flexible criteria based on manual prototype
    target_findings = {
        "description": "Should discover opportunities similar to manual prototype",
        "expected_magnitude": {
            "min_annual_value": 300000,  # $300K
            "max_annual_value": 10000000,  # $10M (allowing for larger discoveries)
        },
        "key_insights": [
            "Equipment performance issues",
            "Financial impact calculation",
            "Specific improvement recommendations"
        ]
    }
    
    # Run flexible validation
    score, details = validate_target_based_response(
        response_text, 
        tool_uses, 
        target_findings
    )
    
    print(f"\nTest: {test_case['eval_id']}")
    print(f"Flexible Validation Score: {score:.1%}")
    print(f"Passed: {'✓' if details['passed'] else '✗'}")
    print(f"Found insights: {details['findings']['found_insights']}")
    print(f"Total value: ${details['findings']['total_value_found']:,}")