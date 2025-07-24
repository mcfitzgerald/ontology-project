"""Guided discovery validator for testing agent with progressive prompting.

This validator mimics how a human analyst would guide discovery through
multi-turn conversations, similar to how the manual prototype was conducted.
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from adk_agents.tests.validation.outcome_evaluator import OutcomeEvaluator
from adk_agents.tests.validation.guided_scenarios import GUIDED_SCENARIOS

logger = logging.getLogger(__name__)


class GuidedDiscoveryValidator:
    """Validates agent performance through guided multi-turn conversations."""
    
    def __init__(self, agent_module_path: str = "adk_agents.manufacturing_agent.agent"):
        self.agent_module_path = agent_module_path
        self.evaluator = OutcomeEvaluator()
        self.runner = None
        self.session_service = None
        self.agent = None
        
        # Track discoveries across conversation
        self.conversation_discoveries = {
            "equipment": set(),
            "products": set(),
            "patterns": set(),
            "root_causes": set(),
            "total_value": 0,
            "insights": []
        }
    
    async def initialize(self):
        """Initialize the agent and runner."""
        # Import agent module
        module_parts = self.agent_module_path.split('.')
        module_path = '.'.join(module_parts[:-1])
        agent_name = module_parts[-1]
        
        module = __import__(module_path, fromlist=[agent_name])
        self.agent = getattr(module, agent_name)
        
        # Create session service and runner
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=self.agent,
            app_name="guided_discovery_test",
            session_service=self.session_service
        )
    
    async def run_guided_scenario(
        self, 
        scenario_id: str, 
        scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run a single guided discovery scenario with multiple conversation turns."""
        logger.info(f"Running guided scenario: {scenario['name']}")
        
        # Create new session for this scenario
        session_id = f"guided_{scenario_id}_{datetime.now().timestamp()}"
        await self.session_service.create_session(
            app_name="guided_discovery_test",
            user_id="test_user",
            session_id=session_id
        )
        
        # Reset conversation discoveries
        self.conversation_discoveries = {
            "equipment": set(),
            "products": set(), 
            "patterns": set(),
            "root_causes": set(),
            "total_value": 0,
            "insights": []
        }
        
        scenario_results = {
            "scenario": scenario_id,
            "name": scenario['name'],
            "steps": [],
            "total_discoveries": {},
            "success": True
        }
        
        # Run each step in sequence
        for step_idx, step in enumerate(scenario['steps']):
            logger.info(f"Step {step_idx + 1}: {step['prompt'][:50]}...")
            
            step_result = await self._run_conversation_step(
                session_id, 
                step, 
                step_idx
            )
            
            scenario_results['steps'].append(step_result)
            
            # Check if we should continue
            if step.get('stop_if_not_found') and not step_result['validations_passed']:
                logger.warning(f"Stopping scenario - required discoveries not found in step {step_idx + 1}")
                scenario_results['success'] = False
                break
        
        # Aggregate total discoveries
        scenario_results['total_discoveries'] = {
            "equipment": list(self.conversation_discoveries['equipment']),
            "products": list(self.conversation_discoveries['products']),
            "patterns": list(self.conversation_discoveries['patterns']),
            "root_causes": list(self.conversation_discoveries['root_causes']),
            "total_value": self.conversation_discoveries['total_value'],
            "insights": self.conversation_discoveries['insights']
        }
        
        return scenario_results
    
    async def _run_conversation_step(
        self, 
        session_id: str,
        step: Dict[str, Any],
        step_idx: int
    ) -> Dict[str, Any]:
        """Run a single conversation step and validate results."""
        start_time = datetime.now()
        
        # Send prompt
        user_message = Content(parts=[Part(text=step['prompt'])])
        
        response_text = ""
        tool_calls = []
        
        try:
            async for event in self.runner.run_async(
                user_id="test_user",
                session_id=session_id,
                new_message=user_message
            ):
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text += part.text
                            
                            if hasattr(part, 'function_call') and part.function_call:
                                tool_calls.append(part.function_call.name)
        
        except Exception as e:
            logger.error(f"Error in step {step_idx + 1}: {e}")
            response_text = f"Error: {str(e)}"
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Extract findings from response
        financial_impact = self.evaluator.extract_financial_impact(response_text)
        entities = self.evaluator.extract_entities(response_text)
        insights = self.evaluator.extract_insights(response_text)
        
        # Combine findings
        findings = {
            'financial_values': financial_impact.get('values', []),
            'total_value': financial_impact.get('total', 0),
            'equipment': entities.get('equipment', []),
            'products': entities.get('products', []),
            'patterns': entities.get('patterns', []),
            'insights': insights
        }
        
        # Update conversation discoveries
        self.conversation_discoveries['equipment'].update(findings['equipment'])
        self.conversation_discoveries['products'].update(findings['products'])
        self.conversation_discoveries['patterns'].update(findings['patterns'])
        self.conversation_discoveries['total_value'] += findings['total_value']
        
        # Check for specific root causes
        root_causes = self._extract_root_causes(response_text)
        self.conversation_discoveries['root_causes'].update(root_causes)
        
        # Validate against expected findings
        validations = self._validate_step(step, findings, response_text)
        
        return {
            "step": step_idx + 1,
            "prompt": step['prompt'],
            "response": response_text[:500] + "..." if len(response_text) > 500 else response_text,
            "execution_time": execution_time,
            "tool_calls": len(tool_calls),
            "findings": findings,
            "validations": validations,
            "validations_passed": all(v['found'] for v in validations if v.get('required', True))
        }
    
    def _extract_root_causes(self, text: str) -> set:
        """Extract root cause mentions from text."""
        root_causes = set()
        
        # Common root cause patterns
        patterns = {
            'jam': ['jam', 'UNP-JAM', 'material jam', 'jamming'],
            'micro-stop': ['micro-stop', 'micro stop', 'microstop', 'brief stop'],
            'foaming': ['foam', 'foaming', 'bubbles'],
            'viscosity': ['viscosity', 'thick', 'flow'],
            'sensor': ['sensor', 'calibration', 'misalignment'],
            'mechanical': ['mechanical', 'wear', 'clearance', 'adjustment']
        }
        
        text_lower = text.lower()
        for cause, keywords in patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                root_causes.add(cause)
        
        return root_causes
    
    def _validate_step(
        self, 
        step: Dict[str, Any], 
        findings: Dict[str, Any],
        response_text: str
    ) -> List[Dict[str, Any]]:
        """Validate findings against step expectations."""
        validations = []
        
        if 'validate' in step:
            for validation in step['validate']:
                result = {"validation": validation, "found": False, "details": ""}
                
                # Check different validation types
                if validation.startswith('$'):
                    # Financial value check
                    threshold = float(validation.replace('$', '').replace(',', ''))
                    if findings['total_value'] >= threshold:
                        result['found'] = True
                        result['details'] = f"Found ${findings['total_value']:,.0f}"
                
                elif 'OEE' in validation:
                    # OEE-related check
                    if any(eq in response_text for eq in findings['equipment']):
                        result['found'] = True
                        result['details'] = f"Found equipment: {', '.join(findings['equipment'])}"
                
                elif validation in ['jam', 'UNP-JAM', 'material jam']:
                    # Root cause check
                    if 'jam' in self.conversation_discoveries['root_causes']:
                        result['found'] = True
                        result['details'] = "Identified jam/material issues"
                
                elif validation in ['night shift', 'shift pattern']:
                    # Pattern check
                    keywords = ['night shift', 'shift', 'overnight', 'third shift']
                    if any(kw in response_text.lower() for kw in keywords):
                        result['found'] = True
                        result['details'] = "Found shift patterns"
                
                elif validation in ['clustering', '10 minutes', 'temporal']:
                    # Time pattern check
                    keywords = ['cluster', 'within minutes', '10 minutes', 'temporal', 'pattern']
                    if any(kw in response_text.lower() for kw in keywords):
                        result['found'] = True
                        result['details'] = "Found temporal patterns"
                
                else:
                    # Generic keyword check
                    if validation.lower() in response_text.lower():
                        result['found'] = True
                        result['details'] = f"Found: {validation}"
                
                validations.append(result)
        
        return validations
    
    async def run_all_scenarios(self) -> Dict[str, Any]:
        """Run all guided discovery scenarios."""
        await self.initialize()
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "scenarios": {},
            "summary": {
                "total_scenarios": len(GUIDED_SCENARIOS),
                "successful": 0,
                "total_value_discovered": 0,
                "key_discoveries": []
            }
        }
        
        for scenario_id, scenario in GUIDED_SCENARIOS.items():
            try:
                scenario_result = await self.run_guided_scenario(scenario_id, scenario)
                results['scenarios'][scenario_id] = scenario_result
                
                if scenario_result['success']:
                    results['summary']['successful'] += 1
                
                # Update summary
                total_value = scenario_result['total_discoveries']['total_value']
                results['summary']['total_value_discovered'] += total_value
                
                # Track key discoveries
                if scenario_result['total_discoveries']['equipment']:
                    results['summary']['key_discoveries'].extend([
                        f"{eq} (${total_value:,.0f})" 
                        for eq in scenario_result['total_discoveries']['equipment']
                    ])
                
            except Exception as e:
                logger.error(f"Error running scenario {scenario_id}: {e}")
                results['scenarios'][scenario_id] = {
                    "error": str(e),
                    "success": False
                }
        
        return results
    
    def generate_comparison_report(
        self, 
        guided_results: Dict[str, Any],
        unguided_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a comparison report between guided and unguided discovery."""
        report = []
        report.append("="*80)
        report.append("GUIDED DISCOVERY VALIDATION REPORT")
        report.append("="*80)
        report.append("")
        
        # Summary
        report.append(f"Timestamp: {guided_results['timestamp']}")
        report.append(f"Scenarios Run: {guided_results['summary']['total_scenarios']}")
        report.append(f"Successful: {guided_results['summary']['successful']}")
        report.append(f"Total Value Discovered: ${guided_results['summary']['total_value_discovered']:,.0f}")
        report.append("")
        
        # Scenario details
        for scenario_id, result in guided_results['scenarios'].items():
            report.append(f"\n{'='*60}")
            report.append(f"Scenario: {result.get('name', scenario_id)}")
            report.append(f"Success: {'✅' if result.get('success') else '❌'}")
            report.append("")
            
            if 'steps' in result:
                for step in result['steps']:
                    report.append(f"Step {step['step']}: {step['prompt'][:60]}...")
                    report.append(f"  Tool calls: {step['tool_calls']}")
                    report.append(f"  Validations: {sum(1 for v in step.get('validations', []) if v['found'])}/{len(step.get('validations', []))}")
                    report.append(f"  Value found: ${step['findings']['total_value']:,.0f}")
                    report.append("")
            
            if 'total_discoveries' in result:
                td = result['total_discoveries']
                report.append("Total Discoveries:")
                report.append(f"  Equipment: {', '.join(td['equipment']) if td['equipment'] else 'None'}")
                report.append(f"  Root Causes: {', '.join(td['root_causes']) if td['root_causes'] else 'None'}")
                report.append(f"  Total Value: ${td['total_value']:,.0f}")
        
        # Comparison with unguided if available
        if unguided_results:
            report.append(f"\n{'='*60}")
            report.append("GUIDED vs UNGUIDED COMPARISON")
            report.append("")
            report.append(f"Unguided Value: ${unguided_results.get('summary', {}).get('total_value_found', 0):,.0f}")
            report.append(f"Guided Value: ${guided_results['summary']['total_value_discovered']:,.0f}")
            report.append(f"Improvement: {(guided_results['summary']['total_value_discovered'] / max(unguided_results.get('summary', {}).get('total_value_found', 1), 1) - 1) * 100:.0f}%")
        
        return "\n".join(report)