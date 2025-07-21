import asyncio
from pathlib import Path
from datetime import datetime
from adk_agents.evaluation.test_agent_evaluation import ManufacturingAgentEvaluator

async def main():
    """Run only the manual prototype validation suite."""
    evaluator = ManufacturingAgentEvaluator()
    
    print("Running Manual Prototype Validation Suite...")
    print("=" * 60)
    
    results = await evaluator.run_evaluation(
        agent_module="adk_agents.manufacturing_agent.agent",
        test_suite="manual_prototype_validation"
    )
    
    # Generate detailed report
    report = evaluator.generate_report()
    print(report)
    
    # Save report
    report_path = Path(__file__).parent / "reports" / f"manual_prototype_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\nReport saved to: {report_path}")
    
    # Detailed findings for manual prototype comparison
    if results['test_results']:
        print("\n\nDETAILED FINDINGS FOR MANUAL PROTOTYPE COMPARISON:")
        print("=" * 60)
        
        for test_id, scores in results['test_results'].items():
            print(f"\n{test_id}:")
            if 'target_validation' in scores:
                print(f"  Target validation score: {scores.get('score', 0):.1%}")
                print(f"  Expected reference: {scores.get('expected_reference', 'N/A')}")
                
                findings = scores.get('findings', {})
                if findings:
                    print(f"  Found insights: {findings.get('found_insights', [])}")
                    print(f"  Total value found: ${findings.get('total_value_found', 0):,}")
                    print(f"  Within target range: {findings.get('within_target_range', False)}")
                    print(f"  Key insights covered: {findings.get('key_insights_covered', 0)}")

if __name__ == "__main__":
    asyncio.run(main())