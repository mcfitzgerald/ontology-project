#!/usr/bin/env python3
"""Main validation runner for testing ADK agent against manual prototype.

This script runs the complete validation suite and generates a detailed report
comparing the agent's discoveries to the manual prototype's $2.5M+ findings.
"""
import asyncio
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from adk_agents.tests.validation.manual_prototype_validator import ManualPrototypeValidator
from adk_agents.tests.validation.outcome_evaluator import OutcomeEvaluator
from adk_agents.tests.validation.scenario_definitions import VALIDATION_SCENARIOS, VALIDATION_CRITERIA


def print_banner():
    """Print validation banner."""
    print("=" * 80)
    print("ADK AGENT VALIDATION AGAINST MANUAL PROTOTYPE")
    print("=" * 80)
    print(f"Target: ${VALIDATION_CRITERIA['financial_discovery_rate'] * 2_500_000:,.0f} ")
    print(f"(>={VALIDATION_CRITERIA['financial_discovery_rate']*100:.0f}% of $2.5M manual prototype)")
    print("=" * 80)
    print()


def print_scenario_result(result: dict, evaluator: OutcomeEvaluator):
    """Print formatted results for a single scenario."""
    print(f"\n{'='*60}")
    print(f"SCENARIO: {result['scenario'].upper()}")
    print(f"{'='*60}")
    print(f"Query: {result['query']}")
    print(f"Execution Time: {result['execution_time']:.2f}s")
    print(f"Tool Calls: {len(result['tool_calls'])}")
    
    # Financial findings
    financial = result['findings']['financial_values']
    if financial:
        print(f"\nFinancial Impact:")
        for val in financial[:3]:  # Show top 3
            print(f"  - {val['text']}")
        print(f"  Total: ${result['findings']['total_value']:,.0f}")
    
    # Key discoveries
    print(f"\nKey Discoveries:")
    if result['findings']['equipment']:
        print(f"  Equipment: {', '.join(result['findings']['equipment'])}")
    if result['findings']['products']:
        print(f"  Products: {', '.join(result['findings']['products'])}")
    if result['findings']['patterns']:
        print(f"  Patterns: {', '.join(result['findings']['patterns'][:5])}")
    
    # Session state
    print(f"\nSession State:")
    print(f"  Discoveries tracked: {result['session_state']['discoveries']}")
    print(f"  Cumulative value: ${result['session_state']['total_value']:,.0f}")


def print_summary_report(report: dict):
    """Print the final validation summary."""
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    summary = report['summary']
    print(f"\nOverall Status: {'✅ PASSED' if summary['overall_passed'] else '❌ FAILED'}")
    print(f"Achievement Rate: {summary['achievement_rate']:.1f}%")
    print(f"Total Value Found: ${summary['total_value_found']:,.0f}")
    print(f"Scenarios Run: {summary['scenarios_run']}")
    print(f"Avg Response Time: {summary['avg_execution_time']:.2f}s")
    
    print("\nValidation Results:")
    for key, validation in report['validations'].items():
        status = "✅" if validation.get('passed', False) else "❌"
        print(f"  {status} {key}:")
        
        # Print relevant details
        if key == "total_value":
            print(f"     Found: ${validation['found']:,.0f} (target: ${validation['target']:,.0f})")
            print(f"     Achievement: {validation['achievement_rate']:.1f}%")
        elif key == "hidden_capacity":
            print(f"     LINE2-PCK found: {validation['equipment_found']}")
            print(f"     Root cause identified: {validation['keywords_found']}")
        elif key == "product_oee":
            print(f"     Energy Drink issue: {validation['energy_drink_found']}")
            print(f"     Premium Juice issue: {validation['premium_juice_found']}")
        elif key == "patterns":
            print(f"     Patterns found: {validation['patterns_found']}")
            if validation['key_patterns']:
                print(f"     Key patterns: {', '.join(validation['key_patterns'])}")
    
    print("\nKey Discoveries:")
    discoveries = report['discoveries']
    if discoveries['equipment']:
        print(f"  Equipment: {', '.join(discoveries['equipment'])}")
    if discoveries['products']:
        print(f"  Products: {', '.join(discoveries['products'])}")
    print(f"  Total patterns: {len(discoveries['patterns'])}")
    
    # Comparison to manual prototype
    print("\n" + "-"*60)
    print("COMPARISON TO MANUAL PROTOTYPE")
    print("-"*60)
    print("Manual Prototype Findings:")
    print("  - LINE2-PCK micro-stops: $341K-$700K")
    print("  - Product OEE issues: $806K")
    print("  - Temporal patterns: $250K-$350K")
    print("  - Quality improvements: $200K")
    print("  - TOTAL: $2.5M+")
    print(f"\nADK Agent Found: ${summary['total_value_found']:,.0f} ({summary['achievement_rate']:.1f}%)")


async def run_validation(save_report: bool = True, verbose: bool = False):
    """Run the complete validation suite."""
    print_banner()
    
    # Initialize validator
    print("Initializing validator...")
    validator = ManualPrototypeValidator()
    evaluator = OutcomeEvaluator()
    
    # Run validation
    print("\nRunning validation scenarios...")
    report = await validator.validate_all_scenarios()
    
    # Print results
    if verbose:
        # Print each scenario result
        for result in report['detailed_results']:
            print_scenario_result(result, evaluator)
    
    # Print summary
    print_summary_report(report)
    
    # Save report
    if save_report:
        validator.save_report(report)
        print(f"\nDetailed report saved to validation directory")
    
    # Return success/failure
    return report['summary']['overall_passed']


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate ADK agent against manual prototype benchmarks"
    )
    parser.add_argument(
        "--no-save", 
        action="store_true",
        help="Don't save the validation report"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed results for each scenario"
    )
    parser.add_argument(
        "--scenario",
        choices=list(VALIDATION_SCENARIOS.keys()),
        help="Run only a specific scenario"
    )
    
    args = parser.parse_args()
    
    # Run validation
    try:
        if args.scenario:
            # Run single scenario
            print(f"Running single scenario: {args.scenario}")
            # TODO: Implement single scenario run
            print("Single scenario mode not yet implemented")
            sys.exit(1)
        else:
            # Run full validation
            success = asyncio.run(run_validation(
                save_report=not args.no_save,
                verbose=args.verbose
            ))
            
            # Exit with appropriate code
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nValidation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()