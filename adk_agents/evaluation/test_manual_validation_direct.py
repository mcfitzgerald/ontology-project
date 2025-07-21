#!/usr/bin/env python3
"""Direct test of manual prototype validation without ADK evaluation framework."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Import the agent and validation functions
from adk_agents.manufacturing_agent.agent import root_agent
from adk_agents.evaluation.flexible_validators import validate_target_based_response
from google.adk.runners import InMemoryRunner
from google.genai import types


async def test_single_prompt(prompt: str, target_findings: Dict[str, Any]) -> Dict[str, Any]:
    """Test a single prompt and validate against target findings."""
    print(f"\n{'='*80}")
    print(f"PROMPT: {prompt}")
    print(f"{'='*80}")
    
    # Create runner
    runner = InMemoryRunner(
        agent=root_agent,
        app_name="manual_validation_test"
    )
    
    # Create session
    user_id = "test_user"
    session_id = f"test_session_{datetime.now().timestamp()}"
    
    await runner.session_service.create_session(
        app_name="manual_validation_test",
        user_id=user_id,
        session_id=session_id
    )
    
    # Run the agent
    response_text = ""
    tool_uses = []
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
    ):
        # Capture function calls (tool uses)
        function_calls = event.get_function_calls()
        if function_calls:
            for fc in function_calls:
                tool_uses.append({
                    'name': fc.name,
                    'args': fc.args,
                    'result': None  # Results come in separate events
                })
        
        # Check for function responses
        function_responses = event.get_function_responses()
        if function_responses:
            # Match responses with calls by name
            for fr in function_responses:
                for tool_use in tool_uses:
                    if tool_use['name'] == fr.name and tool_use['result'] is None:
                        tool_use['result'] = fr.response
                        break
        
        # Check for final response
        if event.is_final_response():
            # Extract final response
            if event.content and event.content.parts:
                response_text = event.content.parts[0].text
            break
    
    print(f"\nRESPONSE:")
    print(response_text)
    
    # Validate against target findings
    score, details = validate_target_based_response(
        response_text, tool_uses, target_findings
    )
    
    print(f"\nVALIDATION RESULTS:")
    print(f"Score: {score:.1%}")
    print(f"Passed: {details['passed']}")
    print(f"Found insights: {details['findings']['found_insights']}")
    print(f"Total value found: ${details['findings']['total_value_found']:,}")
    print(f"Within target range: {details['findings']['within_target_range']}")
    print(f"Key insights covered: {details['findings']['key_insights_covered']}")
    
    return {
        'prompt': prompt,
        'response': response_text,
        'score': score,
        'details': details,
        'tool_uses_count': len(tool_uses)
    }


async def main():
    """Run all manual prototype validation tests."""
    # Load test cases from evalset
    evalset_path = Path(__file__).parent / "evalsets" / "manual_prototype_targets.evalset.json"
    with open(evalset_path, 'r') as f:
        evalset = json.load(f)
    
    results = []
    total_score = 0
    passed_count = 0
    
    print("MANUAL PROTOTYPE VALIDATION - DIRECT TESTING")
    print("=" * 80)
    print(f"Running {len(evalset['eval_cases'])} test cases...")
    
    for case in evalset['eval_cases']:
        conversation = case['conversation'][0]
        prompt = conversation['user_content']['parts'][0]['text']
        target_findings = conversation['target_findings']
        
        result = await test_single_prompt(prompt, target_findings)
        results.append(result)
        
        total_score += result['score']
        if result['details']['passed']:
            passed_count += 1
    
    # Summary report
    print(f"\n{'='*80}")
    print("SUMMARY REPORT")
    print(f"{'='*80}")
    print(f"Total test cases: {len(results)}")
    print(f"Passed: {passed_count}/{len(results)} ({passed_count/len(results)*100:.0f}%)")
    print(f"Average score: {total_score/len(results):.1%}")
    
    print("\nDETAILED RESULTS:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['prompt'][:60]}...")
        print(f"   Score: {result['score']:.1%} - {'PASS' if result['details']['passed'] else 'FAIL'}")
        print(f"   Value found: ${result['details']['findings']['total_value_found']:,}")
        print(f"   Tool uses: {result['tool_uses_count']}")
    
    # Compare with manual prototype
    print(f"\n{'='*80}")
    print("COMPARISON WITH MANUAL PROTOTYPE")
    print(f"{'='*80}")
    print("Manual prototype discovered:")
    print("- $341K-$700K/year from LINE2-PCK capacity (73.2% OEE)")
    print("- $250K-$350K/year from temporal patterns (60% clustering)")
    print("- $200K/year from quality improvements (95.3% -> 98%)")
    print("- Total: $2.5M+ in optimization opportunities")
    
    print("\nAgent discovered:")
    total_value = sum(r['details']['findings']['total_value_found'] for r in results)
    print(f"- Total value found across tests: ${total_value:,}")
    
    # Save detailed report
    report_path = Path(__file__).parent / "reports" / f"direct_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_cases': len(results),
                'passed': passed_count,
                'average_score': total_score / len(results),
                'total_value_found': total_value
            },
            'results': results,
            'manual_prototype_reference': {
                'capacity': "$341K-$700K/year",
                'patterns': "$250K-$350K/year", 
                'quality': "$200K/year",
                'total': "$2.5M+"
            }
        }, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())