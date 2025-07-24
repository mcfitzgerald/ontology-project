#!/usr/bin/env python3
"""Test a single guided discovery scenario."""
import asyncio
import json
import subprocess
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from adk_agents.tests.validation.guided_discovery_validator import GuidedDiscoveryValidator
from adk_agents.tests.validation.guided_scenarios import GUIDED_SCENARIOS

async def test_single_scenario():
    """Test just the LINE2-PCK discovery scenario."""
    print("Starting SPARQL API...")
    api_process = subprocess.Popen(
        ["python", "-m", "uvicorn", "API.main:app", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(5)
    
    try:
        validator = GuidedDiscoveryValidator()
        await validator.initialize()
        
        # Run just the LINE2-PCK scenario
        scenario_id = "line2_pck_deep_dive"
        scenario = GUIDED_SCENARIOS[scenario_id]
        
        print(f"\nRunning scenario: {scenario['name']}")
        print("="*60)
        
        result = await validator.run_guided_scenario(scenario_id, scenario)
        
        # Print results
        print(f"\nSuccess: {'✅' if result['success'] else '❌'}")
        print(f"Total Value Found: ${result['total_discoveries']['total_value']:,.0f}")
        print(f"Equipment Found: {result['total_discoveries']['equipment']}")
        print(f"Root Causes: {result['total_discoveries']['root_causes']}")
        
        # Print step details
        print("\nStep Results:")
        for step in result.get('steps', []):
            print(f"\nStep {step['step']}: {step['prompt'][:60]}...")
            print(f"  Response preview: {step['response'][:150]}...")
            print(f"  Value found: ${step['findings']['total_value']:,.0f}")
            print(f"  Validations passed: {step['validations_passed']}")
            if step.get('validations'):
                for v in step['validations']:
                    print(f"    - {v['validation']}: {'✅' if v['found'] else '❌'} {v.get('details', '')}")
        
        # Save full results
        with open('single_scenario_test.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
        
    finally:
        api_process.terminate()
        api_process.wait()
        print("\nSPARQL API stopped")

if __name__ == "__main__":
    asyncio.run(test_single_scenario())