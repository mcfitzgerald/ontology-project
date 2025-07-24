#!/usr/bin/env python3
"""Run guided discovery validation tests.

This runner executes multi-turn conversations that guide the agent
through progressive discovery, similar to how the manual prototype was conducted.
"""
import asyncio
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from adk_agents.tests.validation.guided_discovery_validator import GuidedDiscoveryValidator
from adk_agents.tests.validation.manual_prototype_validator import ManualPrototypeValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_guided_discovery():
    """Run all guided discovery scenarios."""
    print("="*80)
    print("GUIDED DISCOVERY VALIDATION")
    print("Testing agent with progressive prompting (manual prototype style)")
    print("="*80)
    print()
    
    # Start SPARQL API
    print("Starting SPARQL API...")
    api_process = subprocess.Popen(
        ["python", "-m", "uvicorn", "API.main:app", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for API to start
    time.sleep(5)
    
    try:
        # Initialize validator
        validator = GuidedDiscoveryValidator()
        
        # Run guided scenarios
        print("Running guided discovery scenarios...")
        print()
        
        guided_results = await validator.run_all_scenarios()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path(__file__).parent / f"guided_discovery_report_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(guided_results, f, indent=2)
        
        # Generate report
        report = validator.generate_comparison_report(guided_results)
        print(report)
        
        # Save report
        report_file = Path(__file__).parent / f"guided_discovery_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\nDetailed results saved to: {results_file}")
        print(f"Report saved to: {report_file}")
        
        return guided_results
        
    finally:
        # Stop SPARQL API
        api_process.terminate()
        api_process.wait()
        print("\nSPARQL API stopped")


async def run_comparison():
    """Run both guided and unguided discovery for comparison."""
    print("="*80)
    print("GUIDED vs UNGUIDED DISCOVERY COMPARISON")
    print("="*80)
    print()
    
    # Start SPARQL API
    print("Starting SPARQL API...")
    api_process = subprocess.Popen(
        ["python", "-m", "uvicorn", "API.main:app", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for API to start
    time.sleep(5)
    
    try:
        # Run unguided discovery first
        print("\n1. Running UNGUIDED discovery (single prompts)...")
        print("-"*60)
        
        unguided_validator = ManualPrototypeValidator()
        unguided_results = await unguided_validator.validate_all_scenarios()
        
        print(f"\nUnguided Discovery Results:")
        print(f"  Total Value Found: ${unguided_results['summary']['total_value_found']:,.0f}")
        print(f"  Achievement Rate: {unguided_results['summary']['achievement_rate']:.1f}%")
        
        # Run guided discovery
        print("\n2. Running GUIDED discovery (progressive prompting)...")
        print("-"*60)
        
        guided_validator = GuidedDiscoveryValidator()
        guided_results = await guided_validator.run_all_scenarios()
        
        print(f"\nGuided Discovery Results:")
        print(f"  Total Value Found: ${guided_results['summary']['total_value_discovered']:,.0f}")
        print(f"  Scenarios Successful: {guided_results['summary']['successful']}/{guided_results['summary']['total_scenarios']}")
        
        # Generate comparison
        print("\n3. COMPARISON")
        print("-"*60)
        
        unguided_value = unguided_results['summary']['total_value_found']
        guided_value = guided_results['summary']['total_value_discovered']
        
        print(f"Unguided Value: ${unguided_value:,.0f}")
        print(f"Guided Value: ${guided_value:,.0f}")
        
        if unguided_value > 0:
            improvement = ((guided_value / unguided_value) - 1) * 100
            print(f"Improvement with Guidance: {improvement:+.0f}%")
        
        # Key insights comparison
        print("\nKey Discoveries:")
        print("Unguided:", unguided_results['discoveries'].get('equipment', [])[:3])
        print("Guided:", guided_results['summary'].get('key_discoveries', [])[:3])
        
        # Save comparison report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        comparison_file = Path(__file__).parent / f"discovery_comparison_{timestamp}.json"
        
        comparison_data = {
            "timestamp": datetime.now().isoformat(),
            "unguided": {
                "value": unguided_value,
                "achievement_rate": unguided_results['summary']['achievement_rate'],
                "discoveries": unguided_results['discoveries']
            },
            "guided": {
                "value": guided_value,
                "successful_scenarios": guided_results['summary']['successful'],
                "key_discoveries": guided_results['summary']['key_discoveries']
            },
            "improvement": {
                "value_increase": guided_value - unguided_value,
                "percentage": ((guided_value / max(unguided_value, 1)) - 1) * 100
            }
        }
        
        with open(comparison_file, 'w') as f:
            json.dump(comparison_data, f, indent=2)
        
        print(f"\nComparison saved to: {comparison_file}")
        
        return comparison_data
        
    finally:
        # Stop SPARQL API
        api_process.terminate()
        api_process.wait()
        print("\nSPARQL API stopped")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run guided discovery validation")
    parser.add_argument(
        '--compare', 
        action='store_true',
        help='Run comparison between guided and unguided discovery'
    )
    parser.add_argument(
        '--scenario',
        help='Run a specific scenario (e.g., line2_pck_deep_dive)'
    )
    
    args = parser.parse_args()
    
    if args.compare:
        asyncio.run(run_comparison())
    else:
        asyncio.run(run_guided_discovery())


if __name__ == "__main__":
    main()