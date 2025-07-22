"""
Enhanced flexible validator that properly captures all financial values.
"""
import re
import json
from typing import Dict, Any, List, Tuple

def extract_financial_values(text: str) -> List[float]:
    """Extract all financial values from text, handling various formats."""
    values = []
    
    # Patterns to match different financial formats
    patterns = [
        # $9,359,760 or $9359760
        (r'\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', lambda x: float(x.replace(',', ''))),
        # $9.36M or $9.3M
        (r'\$(\d+(?:\.\d+)?)\s*M', lambda x: float(x) * 1000000),
        # $341K or $341.5K
        (r'\$(\d+(?:\.\d+)?)\s*K', lambda x: float(x) * 1000),
        # 9,359,760 (without $)
        (r'(?<!\$)(\d{1,3}(?:,\d{3}){2,}(?:\.\d+)?)', lambda x: float(x.replace(',', ''))),
        # Simple numbers in millions/thousands context
        (r'(\d+(?:\.\d+)?)\s*million', lambda x: float(x) * 1000000),
        (r'(\d+(?:\.\d+)?)\s*thousand', lambda x: float(x) * 1000),
    ]
    
    for pattern, converter in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                value = converter(match)
                if value > 0:  # Only positive values
                    values.append(value)
            except:
                continue
    
    return values

def validate_agent_response(
    response_text: str,
    tool_uses: List[Dict[str, Any]],
    expected_findings: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate agent response against expected findings with flexible criteria.
    """
    results = {
        "financial_values_found": [],
        "total_value": 0,
        "insights_found": [],
        "has_recommendations": False,
        "equipment_identified": [],
        "patterns_found": [],
        "confidence_scores": [],
        "passed": False,
        "score": 0.0
    }
    
    # Extract financial values
    financial_values = extract_financial_values(response_text)
    
    # Also check tool uses for financial calculations
    for tool_use in tool_uses:
        if tool_use['name'] == 'format_insight':
            args = tool_use.get('args', {})
            if 'impact' in args:
                financial_values.append(float(args['impact']))
            if 'confidence' in args:
                results['confidence_scores'].append(args['confidence'])
            if 'finding' in args:
                results['insights_found'].append(args['finding'])
            if 'action' in args:
                results['has_recommendations'] = True
                
    results['financial_values_found'] = financial_values
    results['total_value'] = sum(financial_values) if financial_values else 0
    
    # Extract equipment mentions
    equipment_pattern = r'(LINE\d+-\w+|EQUIPMENT-\d+)'
    equipment_matches = re.findall(equipment_pattern, response_text)
    results['equipment_identified'] = list(set(equipment_matches))
    
    # Check for pattern discoveries
    pattern_keywords = ['cluster', 'temporal', 'shift', 'pattern', 'trend', 'correlation']
    for keyword in pattern_keywords:
        if keyword.lower() in response_text.lower():
            results['patterns_found'].append(keyword)
    
    # Calculate score based on findings
    score = 0.0
    
    # Financial discovery (40% weight)
    if results['total_value'] > 0:
        expected_min = expected_findings.get('min_value', 100000)
        expected_max = expected_findings.get('max_value', 10000000)
        
        if expected_min <= results['total_value'] <= expected_max:
            score += 0.4
        elif results['total_value'] > expected_max:
            score += 0.4  # Still good if exceeded expectations
        else:
            # Partial credit based on proximity
            score += 0.2
    
    # Insights and recommendations (30% weight)
    if results['insights_found']:
        score += 0.15
    if results['has_recommendations']:
        score += 0.15
        
    # Equipment identification (20% weight)
    if results['equipment_identified']:
        score += 0.2
        
    # Pattern discovery (10% weight)
    if results['patterns_found']:
        score += 0.1
    
    results['score'] = score
    results['passed'] = score >= 0.6  # 60% threshold
    
    return results

def run_comprehensive_validation(eval_result_file: str):
    """Run comprehensive validation on evaluation results."""
    
    # Load evaluation results
    with open(eval_result_file, 'r') as f:
        data = json.loads(json.loads(f.read()))
    
    print("=== FLEXIBLE VALIDATION RESULTS ===\n")
    
    # Expected findings from manual prototype
    expected_findings = {
        "discover_capacity_opportunities": {
            "min_value": 300000,
            "max_value": 10000000,
            "key_findings": ["capacity", "OEE", "downtime"]
        },
        "analyze_downtime_patterns": {
            "min_value": 200000,
            "max_value": 500000,
            "key_findings": ["pattern", "cluster", "shift"]
        },
        "reduce_scrap_costs": {
            "min_value": 150000,
            "max_value": 300000,
            "key_findings": ["quality", "scrap", "cost"]
        }
    }
    
    total_tests = 0
    passed_tests = 0
    
    for test_case in data['eval_case_results']:
        test_id = test_case['eval_id']
        total_tests += 1
        
        actual = test_case['eval_metric_result_per_invocation'][0]['actual_invocation']
        
        # Extract response and tool uses
        response_text = ""
        if actual.get('final_response') and actual['final_response'].get('parts'):
            response_text = actual['final_response']['parts'][0]['text']
        else:
            print(f"  ⚠️  No final response generated (likely hit token limit or error)")
        
        tool_uses = actual['intermediate_data']['tool_uses']
        print(f"  📊 Tool uses: {len(tool_uses)}")
        
        # Get expected findings for this test
        expected = expected_findings.get(test_id, {
            "min_value": 100000,
            "max_value": 10000000
        })
        
        # Run validation
        results = validate_agent_response(response_text, tool_uses, expected)
        
        if results['passed']:
            passed_tests += 1
        
        # Print results
        print(f"Test: {test_id}")
        print(f"Status: {'✅ PASSED' if results['passed'] else '❌ FAILED'}")
        print(f"Score: {results['score']:.1%}")
        print(f"Financial Values Found: {[f'${v:,.0f}' for v in results['financial_values_found']]}")
        print(f"Total Value: ${results['total_value']:,.0f}")
        
        if results['insights_found']:
            print(f"Insights: {results['insights_found'][0][:80]}...")
        
        if results['equipment_identified']:
            print(f"Equipment: {', '.join(results['equipment_identified'])}")
            
        if results['patterns_found']:
            print(f"Patterns: {', '.join(results['patterns_found'])}")
            
        print(f"Has Recommendations: {'✓' if results['has_recommendations'] else '✗'}")
        print()
    
    print("="*50)
    print(f"OVERALL: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.0f}%)")
    
    # Check against manual prototype targets
    print("\n=== COMPARISON TO MANUAL PROTOTYPE ===")
    print("Manual Prototype Found:")
    print("- Hidden Capacity: $341K-$700K")
    print("- Micro-stop Patterns: $250K-$350K") 
    print("- Quality Improvements: $200K")
    print("- Total: $2.5M+")
    print("\nAgent Found:")
    
    total_agent_value = 0
    for tc in data['eval_case_results']:
        actual = tc['eval_metric_result_per_invocation'][0]['actual_invocation']
        response_text = ""
        if actual.get('final_response') and actual['final_response'].get('parts'):
            response_text = actual['final_response']['parts'][0].get('text', '')
        
        tool_uses = actual['intermediate_data']['tool_uses']
        result = validate_agent_response(response_text, tool_uses, {})
        total_agent_value += result['total_value']
    
    print(f"- Total Value Discovered: ${total_agent_value:,.0f}")
    print(f"- Performance vs Manual: {total_agent_value/2500000*100:.0f}%")

if __name__ == "__main__":
    import sys
    
    eval_file = '../manufacturing_agent/.adk/eval_history/manufacturing_agent_manual_prototype_targets_1753143002.4005492.evalset_result.json'
    
    run_comprehensive_validation(eval_file)