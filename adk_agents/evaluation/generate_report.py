#!/usr/bin/env python3
"""
Standalone report generator for ADK Manufacturing Agent evaluation results

This utility can be used to generate human-readable reports from evaluation results
or to create summary reports across multiple evaluation runs.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class ReportGenerator:
    """Generate various types of evaluation reports"""
    
    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = Path(__file__).parent / reports_dir
        self.reports_dir.mkdir(exist_ok=True)
        
    def generate_summary_report(self, results: Dict) -> str:
        """Generate a concise summary report"""
        timestamp = results.get('timestamp', datetime.now().isoformat())
        agent = results.get('agent_module', 'Unknown')
        test_suite = results.get('test_suite', 'Unknown')
        passed = results.get('passed', False)
        
        report = f"""
ADK MANUFACTURING AGENT EVALUATION SUMMARY
==========================================
Date: {timestamp}
Agent: {agent}
Test Suite: {test_suite}
Result: {'✅ PASS' if passed else '❌ FAIL'}

Key Metrics:
"""
        
        scores = results.get('overall_scores', {})
        for metric, score in scores.items():
            if metric != 'weighted_total':
                report += f"  • {metric.replace('_', ' ').title()}: {score:.1%}\n"
                
        report += f"\nOverall Score: {scores.get('weighted_total', 0):.1%}\n"
        
        return report
    
    def generate_detailed_report(self, results: Dict) -> str:
        """Generate a detailed report with test case breakdowns"""
        report = f"""
=== DETAILED EVALUATION REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

AGENT INFORMATION
-----------------
Module: {results.get('agent_module', 'Unknown')}
Test Suite: {results.get('test_suite', 'Unknown')}
Evaluation Time: {results.get('timestamp', 'Unknown')}

TEST RESULTS BY CATEGORY
------------------------
"""
        
        test_results = results.get('test_results', {})
        
        for test_id, scores in test_results.items():
            report += f"\n{test_id.upper().replace('_', ' ')}:\n"
            report += "-" * (len(test_id) + 1) + "\n"
            
            for metric, score in scores.items():
                report += f"  {metric.replace('_', ' ').title()}: {score:.1%}\n"
                
                # Add specific insights based on metric
                if metric == 'discovery_first' and score < 0.9:
                    report += "    ⚠️  Agent should start with entity discovery queries\n"
                elif metric == 'proactive_execution' and score < 0.85:
                    report += "    ⚠️  Agent is asking for too many confirmations\n"
                elif metric == 'financial_accuracy' and score < 0.8:
                    report += "    ⚠️  Financial calculations need improvement\n"
                    
        # Add recommendations
        report += "\nRECOMMENDATIONS\n"
        report += "---------------\n"
        
        if results.get('passed'):
            report += "✅ Agent is performing well across all metrics.\n"
            report += "Consider:\n"
            report += "  • Testing with more complex scenarios\n"
            report += "  • Evaluating response time optimization\n"
            report += "  • Adding domain-specific test cases\n"
        else:
            report += "❌ Agent needs improvement in the following areas:\n"
            
            scores = results.get('overall_scores', {})
            if scores.get('discovery_first', 1.0) < 0.9:
                report += "\n1. Discovery-First Pattern:\n"
                report += "   - Always start with SELECT DISTINCT queries\n"
                report += "   - Discover entities before building complex queries\n"
                report += "   - Validate entity names against the ontology\n"
                
            if scores.get('proactive_execution', 1.0) < 0.85:
                report += "\n2. Proactive Execution:\n"
                report += "   - Execute analysis queries immediately\n"
                report += "   - Only ask for confirmation on destructive operations\n"
                report += "   - Remove phrases like 'Should I execute this query?'\n"
                
            if scores.get('financial_accuracy', 1.0) < 0.8:
                report += "\n3. Financial Analysis:\n"
                report += "   - Always calculate ROI for improvements\n"
                report += "   - Use product margins in calculations\n"
                report += "   - Annualize daily savings for impact\n"
                
        return report
    
    def generate_comparison_report(self, results_list: List[Dict]) -> str:
        """Generate a report comparing multiple evaluation runs"""
        report = """
COMPARATIVE EVALUATION REPORT
=============================

This report compares multiple evaluation runs to track improvement over time.

"""
        
        # Create comparison table
        report += "Run # | Date/Time           | Test Suite      | Overall Score | Result\n"
        report += "-" * 70 + "\n"
        
        for i, results in enumerate(results_list, 1):
            timestamp = results.get('timestamp', 'Unknown')[:19]
            test_suite = results.get('test_suite', 'Unknown')[:15]
            overall_score = results.get('overall_scores', {}).get('weighted_total', 0)
            passed = "PASS" if results.get('passed') else "FAIL"
            
            report += f"{i:4d} | {timestamp:19s} | {test_suite:15s} | {overall_score:12.1%} | {passed}\n"
            
        # Add trend analysis
        report += "\nTREND ANALYSIS\n"
        report += "--------------\n"
        
        if len(results_list) > 1:
            first_score = results_list[0].get('overall_scores', {}).get('weighted_total', 0)
            last_score = results_list[-1].get('overall_scores', {}).get('weighted_total', 0)
            improvement = last_score - first_score
            
            if improvement > 0:
                report += f"✅ Overall improvement: +{improvement:.1%}\n"
            elif improvement < 0:
                report += f"❌ Overall regression: {improvement:.1%}\n"
            else:
                report += "➖ No change in overall performance\n"
                
        return report
    
    def save_report(self, content: str, filename: Optional[str] = None) -> Path:
        """Save report to file"""
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
        filepath = self.reports_dir / filename
        with open(filepath, 'w') as f:
            f.write(content)
            
        return filepath


def main():
    """CLI interface for report generation"""
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <results.json> [report_type]")
        print("Report types: summary (default), detailed, comparison")
        sys.exit(1)
        
    results_file = sys.argv[1]
    report_type = sys.argv[2] if len(sys.argv) > 2 else "summary"
    
    generator = ReportGenerator()
    
    # Load results
    with open(results_file, 'r') as f:
        results = json.load(f)
        
    # Generate appropriate report
    if report_type == "summary":
        report = generator.generate_summary_report(results)
    elif report_type == "detailed":
        report = generator.generate_detailed_report(results)
    elif report_type == "comparison":
        # For comparison, expect a list of result files
        all_results = []
        for arg in sys.argv[1:]:
            if arg.endswith('.json'):
                with open(arg, 'r') as f:
                    all_results.append(json.load(f))
        report = generator.generate_comparison_report(all_results)
    else:
        print(f"Unknown report type: {report_type}")
        sys.exit(1)
        
    # Save and display report
    filepath = generator.save_report(report)
    print(report)
    print(f"\nReport saved to: {filepath}")


if __name__ == "__main__":
    main()