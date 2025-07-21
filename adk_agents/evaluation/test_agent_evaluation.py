"""
Manufacturing Agent Evaluation Suite

This module provides comprehensive evaluation of the manufacturing analyst agents
against proven patterns from the $2.5M optimization case study.
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import pytest
from google.adk.evaluation.agent_evaluator import AgentEvaluator


class ManufacturingAgentEvaluator:
    """Extended evaluator with custom metrics for manufacturing agents"""
    
    def __init__(self, config_path: str = "test_config.json"):
        """Initialize evaluator with configuration"""
        self.config_path = Path(__file__).parent / config_path
        self.load_config()
        self.results = {}
        
    def load_config(self):
        """Load evaluation configuration"""
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
            
    @staticmethod
    def evaluate_discovery_first(trajectory: Dict[str, Any]) -> float:
        """
        Check if agent starts with entity discovery before complex queries
        
        Returns:
            Score from 0.0 to 1.0 indicating compliance
        """
        tool_uses = trajectory.get('intermediate_data', {}).get('tool_uses', [])
        if not tool_uses:
            return 0.0
            
        # Check first few queries for discovery patterns
        discovery_patterns = [
            'SELECT DISTINCT',
            '?line WHERE',
            '?equipment WHERE',
            'belongsToLine',
            'a mes_ontology_populated:Line'
        ]
        
        first_queries = tool_uses[:3]
        discovery_count = 0
        
        for query in first_queries:
            if query.get('name') == 'execute_sparql_query':
                query_text = query.get('args', {}).get('query', '')
                if any(pattern in query_text for pattern in discovery_patterns):
                    discovery_count += 1
                    
        # Score based on discovery queries in first 3 tool uses
        return min(discovery_count / 2.0, 1.0)
    
    @staticmethod
    def evaluate_proactive_execution(trajectory: Dict[str, Any]) -> float:
        """
        Check if agent executes queries proactively without confirmation prompts
        
        Returns:
            Score from 0.0 to 1.0 indicating proactive behavior
        """
        response_text = trajectory.get('final_response', {}).get('parts', [{}])[0].get('text', '')
        tool_uses = trajectory.get('intermediate_data', {}).get('tool_uses', [])
        
        # Negative indicators (asking for confirmation)
        confirmation_phrases = [
            "Should I execute",
            "Would you like me to run",
            "Shall I proceed",
            "Do you want me to execute",
            "I'm now executing"  # This followed by waiting is bad
        ]
        
        # Check for confirmation requests
        confirmations_found = sum(1 for phrase in confirmation_phrases if phrase.lower() in response_text.lower())
        
        # Positive indicator: queries executed relative to discussion
        queries_executed = len([t for t in tool_uses if t.get('name') == 'execute_sparql_query'])
        
        if queries_executed == 0:
            return 0.0
            
        # Penalize for confirmation requests
        penalty = confirmations_found * 0.2
        score = max(0.0, 1.0 - penalty)
        
        return score
    
    @staticmethod
    def evaluate_financial_accuracy(trajectory: Dict[str, Any], expected_range: Tuple[float, float]) -> float:
        """
        Check if calculated ROI falls within expected range
        
        Args:
            trajectory: Agent execution trajectory
            expected_range: (min_roi, max_roi) tuple
            
        Returns:
            Score from 0.0 to 1.0 indicating accuracy
        """
        tool_uses = trajectory.get('intermediate_data', {}).get('tool_uses', [])
        
        # Look for ROI calculations
        roi_calculations = [
            t for t in tool_uses 
            if t.get('name') == 'calculate_improvement_roi'
        ]
        
        if not roi_calculations:
            # Check if ROI is mentioned in response
            response_text = trajectory.get('final_response', {}).get('parts', [{}])[0].get('text', '')
            roi_values = []
            
            # Simple extraction of dollar amounts
            import re
            dollar_amounts = re.findall(r'\$(\d+)K', response_text)
            for amount in dollar_amounts:
                roi_values.append(float(amount) * 1000)
                
            if not roi_values:
                return 0.0
        else:
            # Extract ROI from tool calls
            roi_values = []
            for calc in roi_calculations:
                args = calc.get('args', {})
                # Estimate ROI based on performance improvement
                current = args.get('current_performance', 0)
                target = args.get('target_performance', 0)
                daily_value = args.get('production_value_per_day', 0)
                
                if current and target and daily_value:
                    improvement_pct = (target - current) / 100.0
                    annual_roi = daily_value * improvement_pct * 365
                    roi_values.append(annual_roi)
        
        if not roi_values:
            return 0.0
            
        # Check if any calculated ROI falls within expected range
        min_roi, max_roi = expected_range
        for roi in roi_values:
            if min_roi <= roi <= max_roi:
                return 1.0
                
        # Partial credit for being close
        closest_roi = min(roi_values, key=lambda x: min(abs(x - min_roi), abs(x - max_roi)))
        if closest_roi < min_roi:
            distance_ratio = closest_roi / min_roi
        else:
            distance_ratio = max_roi / closest_roi
            
        return max(0.0, distance_ratio)
    
    @staticmethod
    def evaluate_pattern_recognition(trajectory: Dict[str, Any], expected_patterns: Dict[str, Any]) -> float:
        """
        Check if agent identifies expected patterns in data
        
        Args:
            trajectory: Agent execution trajectory
            expected_patterns: Dictionary of expected pattern findings
            
        Returns:
            Score from 0.0 to 1.0 indicating pattern recognition quality
        """
        response_text = trajectory.get('final_response', {}).get('parts', [{}])[0].get('text', '')
        tool_uses = trajectory.get('intermediate_data', {}).get('tool_uses', [])
        
        # Check for analysis tool usage
        analysis_calls = [
            t for t in tool_uses 
            if t.get('name') == 'analyze_patterns'
        ]
        
        patterns_found = 0
        total_patterns = len(expected_patterns)
        
        # Check response for pattern mentions
        for pattern_key, pattern_value in expected_patterns.items():
            if pattern_key == 'clustering_percent':
                if '60%' in response_text or 'sixty percent' in response_text.lower():
                    patterns_found += 1
            elif pattern_key == 'shift_variance_percent':
                if '40%' in response_text or 'forty percent' in response_text.lower():
                    patterns_found += 1
            elif pattern_key == 'annual_opportunity':
                if str(pattern_value) in response_text or f"{pattern_value/1000}K" in response_text:
                    patterns_found += 1
                    
        # Bonus for using analysis tools
        if analysis_calls:
            patterns_found += 0.5
            
        return min(patterns_found / total_patterns, 1.0)
    
    async def run_evaluation(self, agent_module: str, test_suite: str = "full_suite"):
        """
        Run evaluation for specified test suite
        
        Args:
            agent_module: Path to agent module
            test_suite: Name of test suite to run
        """
        evalset_dir = Path(__file__).parent / "evalsets"
        test_files = self.config['test_suites'].get(test_suite, [])
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'agent_module': agent_module,
            'test_suite': test_suite,
            'test_results': {},
            'overall_scores': {},
            'passed': False
        }
        
        for test_file in test_files:
            test_path = evalset_dir / test_file
            
            # Run ADK evaluation
            await AgentEvaluator.evaluate(
                agent_module=agent_module,
                eval_dataset_file_path_or_dir=str(test_path),
            )
            
            # Load results and apply custom metrics
            with open(test_path, 'r') as f:
                test_data = json.load(f)
                
            test_id = test_data['eval_set_id']
            results['test_results'][test_id] = self._evaluate_custom_metrics(test_data)
            
        # Calculate overall scores
        results['overall_scores'] = self._calculate_overall_scores(results['test_results'])
        results['passed'] = self._check_pass_criteria(results['overall_scores'])
        
        self.results = results
        return results
    
    def _evaluate_custom_metrics(self, test_data: Dict[str, Any]) -> Dict[str, float]:
        """Apply custom metrics to test data"""
        scores = {}
        
        for eval_case in test_data.get('eval_cases', []):
            for conversation in eval_case.get('conversation', []):
                # Check if we have flexible validation criteria
                if 'validation_criteria' in conversation:
                    # Use flexible validators
                    from .flexible_validators import validate_response
                    
                    validation_type = conversation['validation_criteria']['type']
                    response_text = conversation.get('final_response', {}).get('parts', [{}])[0].get('text', '')
                    tool_uses = conversation.get('intermediate_data', {}).get('tool_uses', [])
                    criteria = conversation['validation_criteria']['required_findings']
                    
                    score, details = validate_response(
                        validation_type, response_text, tool_uses, criteria
                    )
                    
                    scores[f'{validation_type}_score'] = score
                    scores['flexible_validation'] = score
                else:
                    # Use original metrics
                    # Discovery-first compliance
                    scores['discovery_first'] = self.evaluate_discovery_first(conversation)
                    
                    # Proactive execution
                    scores['proactive_execution'] = self.evaluate_proactive_execution(conversation)
                    
                    # Financial accuracy (if applicable)
                    if 'hidden_capacity' in test_data['eval_set_id']:
                        expected_range = (
                            self.config['expected_outcomes']['hidden_capacity']['min_roi'],
                            self.config['expected_outcomes']['hidden_capacity']['max_roi']
                        )
                        scores['financial_accuracy'] = self.evaluate_financial_accuracy(
                            conversation, expected_range
                        )
                        
                    # Pattern recognition (if applicable)
                    if 'microstop' in test_data['eval_set_id']:
                        expected_patterns = self.config['expected_outcomes']['microstop_patterns']
                        scores['pattern_recognition'] = self.evaluate_pattern_recognition(
                            conversation, expected_patterns
                        )
                    
        return scores
    
    def _calculate_overall_scores(self, test_results: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Calculate weighted overall scores"""
        all_scores = {}
        weights = self.config['scoring_weights']
        
        # Aggregate scores across all tests
        for test_id, scores in test_results.items():
            for metric, score in scores.items():
                if metric not in all_scores:
                    all_scores[metric] = []
                all_scores[metric].append(score)
                
        # Calculate weighted average
        overall = {}
        for metric, scores in all_scores.items():
            overall[metric] = sum(scores) / len(scores) if scores else 0.0
            
        # Calculate final weighted score
        weighted_score = 0.0
        weight_map = {
            'discovery_first': weights['discovery_compliance'],
            'proactive_execution': weights['proactive_behavior'],
            'financial_accuracy': weights['financial_accuracy']
        }
        
        for metric, weight_key in weight_map.items():
            if metric in overall:
                weighted_score += overall[metric] * weight_key
                
        overall['weighted_total'] = weighted_score
        
        return overall
    
    def _check_pass_criteria(self, scores: Dict[str, float]) -> bool:
        """Check if scores meet passing criteria"""
        criteria = self.config['criteria']['custom_metrics']
        
        for metric, min_score in criteria.items():
            if metric in scores and scores[metric] < min_score:
                return False
                
        return True
    
    def generate_report(self) -> str:
        """Generate human-readable evaluation report"""
        if not self.results:
            return "No evaluation results available. Run evaluation first."
            
        results = self.results
        report = f"""
=== ADK Manufacturing Agent Evaluation Report ===
Date: {results['timestamp']}
Agent: {results['agent_module']}
Test Suite: {results['test_suite']}

OVERALL RESULT: {'PASS' if results['passed'] else 'FAIL'}

DETAILED SCORES:
"""
        
        # Add test-specific results
        for test_id, scores in results['test_results'].items():
            report += f"\n{test_id.upper().replace('_', ' ')}:\n"
            for metric, score in scores.items():
                status = "✓" if score >= 0.75 else "✗"
                report += f"  {status} {metric.replace('_', ' ').title()}: {score:.1%}\n"
                
        # Add overall scores
        report += "\nOVERALL METRICS:\n"
        for metric, score in results['overall_scores'].items():
            if metric != 'weighted_total':
                required = self.config['criteria']['custom_metrics'].get(
                    metric, 0.75
                )
                status = "✓" if score >= required else "✗"
                report += f"  {status} {metric.replace('_', ' ').title()}: {score:.1%} (required: {required:.0%})\n"
                
        report += f"\nWEIGHTED TOTAL SCORE: {results['overall_scores'].get('weighted_total', 0):.1%}\n"
        
        # Add insights
        if results['passed']:
            report += "\n✅ Agent successfully demonstrates:\n"
            report += "  - Discovery-first approach to query building\n"
            report += "  - Proactive execution without unnecessary confirmations\n"
            report += "  - Accurate financial impact calculations\n"
            report += "  - Pattern recognition capabilities\n"
        else:
            report += "\n❌ Areas for improvement:\n"
            for metric, score in results['overall_scores'].items():
                if metric != 'weighted_total':
                    required = self.config['criteria']['custom_metrics'].get(metric, 0.75)
                    if score < required:
                        report += f"  - {metric.replace('_', ' ').title()}: {score:.1%} < {required:.0%} required\n"
        
        return report


# Pytest integration
@pytest.mark.asyncio
async def test_discovery_first_pattern():
    """Test that agent follows discovery-first pattern"""
    evaluator = ManufacturingAgentEvaluator()
    results = await evaluator.run_evaluation(
        agent_module="manufacturing_agent",
        test_suite="core_functionality"
    )
    assert results['passed'], "Discovery-first pattern test failed"


@pytest.mark.asyncio
async def test_financial_analysis():
    """Test agent's financial analysis capabilities"""
    evaluator = ManufacturingAgentEvaluator()
    results = await evaluator.run_evaluation(
        agent_module="manufacturing_agent",
        test_suite="financial_analysis"
    )
    assert results['passed'], "Financial analysis test failed"


@pytest.mark.asyncio
async def test_pattern_recognition():
    """Test agent's pattern recognition capabilities"""
    evaluator = ManufacturingAgentEvaluator()
    results = await evaluator.run_evaluation(
        agent_module="manufacturing_agent",
        test_suite="pattern_recognition"
    )
    assert results['passed'], "Pattern recognition test failed"


@pytest.mark.asyncio
async def test_full_suite():
    """Run complete evaluation suite"""
    evaluator = ManufacturingAgentEvaluator()
    results = await evaluator.run_evaluation(
        agent_module="manufacturing_agent",
        test_suite="full_suite"
    )
    
    # Generate and print report
    report = evaluator.generate_report()
    print(report)
    
    # Save report
    report_path = Path(__file__).parent / "reports" / f"evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report)
        
    assert results['passed'], "Full evaluation suite failed"


if __name__ == "__main__":
    # Run evaluation directly
    async def main():
        evaluator = ManufacturingAgentEvaluator()
        results = await evaluator.run_evaluation(
            agent_module="manufacturing_agent",
            test_suite="full_suite"
        )
        print(evaluator.generate_report())
        
    asyncio.run(main())