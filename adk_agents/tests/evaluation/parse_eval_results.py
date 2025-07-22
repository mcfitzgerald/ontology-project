import json

# Load the evaluation results
with open('manufacturing_agent/.adk/eval_history/manufacturing_agent_manual_prototype_targets_1753143002.4005492.evalset_result.json', 'r') as f:
    content = f.read()
    # The file contains a JSON string that needs to be parsed twice
    data = json.loads(json.loads(content))

# Extract findings from first test case
test_case = data['eval_case_results'][0]
actual = test_case['eval_metric_result_per_invocation'][0]['actual_invocation']

print("=== EVALUATION RESULTS ===")
print(f"Test: {test_case['eval_id']}")
print(f"User Query: {actual['user_content']['parts'][0]['text']}")
print("\n=== AGENT'S RESPONSE ===")
if actual.get('final_response'):
    print(actual['final_response']['parts'][0]['text'])

# Look at the tools used
print("\n=== DISCOVERIES MADE ===")
for tool_use in actual['intermediate_data']['tool_uses']:
    if tool_use['name'] == 'format_insight':
        args = tool_use['args']
        print(f"\nFinding: {args['finding']}")
        print(f"Impact: ${args['impact']:,.2f}")
        print(f"Action: {args['action']}")
        print(f"Evidence: {args['evidence']}")
        print(f"Confidence: {args['confidence']*100}%")