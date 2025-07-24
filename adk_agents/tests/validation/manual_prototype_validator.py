"""Core validation class for testing ADK agent against manual prototype benchmarks.

This validator runs the agent through business scenarios and compares outcomes
(not execution paths) to the manual prototype's $2.5M+ discoveries.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import re

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

logger = logging.getLogger(__name__)


class ManualPrototypeValidator:
    """Validates ADK agent against manual prototype discoveries."""
    
    def __init__(self, agent_module_path: str = "adk_agents.manufacturing_agent.agent"):
        """Initialize validator with agent module path.
        
        Args:
            agent_module_path: Python module path to the agent (default: manufacturing agent)
        """
        self.agent_module_path = agent_module_path
        self.session_service = InMemorySessionService()
        self.runner = None
        self.validation_results = []
        
        # Manual prototype benchmarks from Reference/manual_prototype.md
        self.benchmarks = {
            "total_value": 2_500_000,  # $2.5M+ target
            "hidden_capacity": {
                "min": 341_000,
                "max": 700_000,
                "equipment": "LINE2-PCK",
                "root_cause": ["jam", "micro-stop", "UNP-JAM"]
            },
            "product_oee": {
                "total": 806_000,
                "issues": {
                    "Energy Drink": 710_000,  # Foaming issue
                    "Premium Juice": 97_000   # Scrap issue
                }
            },
            "temporal_patterns": {
                "min": 250_000,
                "max": 350_000,
                "patterns": ["cascade", "cluster", "10 minutes", "night shift"]
            },
            "quality_tradeoff": {
                "value": 200_000,
                "focus": ["scrap", "quality", "margin"]
            }
        }
    
    async def setup(self):
        """Set up the runner and session for testing."""
        # Dynamically import the agent
        module_parts = self.agent_module_path.split('.')
        module_name = '.'.join(module_parts[:-1])
        agent_name = module_parts[-1]
        
        module = __import__(module_name, fromlist=[agent_name])
        agent = getattr(module, agent_name)
        
        # Create runner
        self.runner = Runner(
            agent=agent,
            app_name="validation_test",
            session_service=self.session_service
        )
        
        # Create session
        self.session = await self.session_service.create_session(
            app_name="validation_test",
            user_id="validator",
            session_id=f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        logger.info(f"Validation setup complete. Session: {self.session.id}")
    
    async def run_scenario(self, scenario_name: str, query: str) -> Dict:
        """Run a single scenario and collect results.
        
        Args:
            scenario_name: Name of the scenario for tracking
            query: Business question to ask the agent
            
        Returns:
            Dict with scenario results including response and extracted values
        """
        logger.info(f"Running scenario: {scenario_name}")
        logger.info(f"Query: {query}")
        
        # Create user message
        user_message = Content(parts=[Part(text=query)])
        
        # Collect full response
        response_text = ""
        tool_calls = []
        
        start_time = datetime.now()
        
        async for event in self.runner.run_async(
            user_id=self.session.user_id,
            session_id=self.session.id,
            new_message=user_message
        ):
            # Collect response text
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text
            
            # Track tool calls
            if hasattr(event, 'type') and event.type == 'tool_call':
                tool_calls.append({
                    'tool': getattr(event, 'tool_name', 'unknown'),
                    'timestamp': datetime.now().isoformat()
                })
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Extract findings from response
        findings = self._extract_findings(response_text)
        
        # Get session state
        updated_session = await self.session_service.get_session(
            app_name="validation_test",
            user_id=self.session.user_id,
            session_id=self.session.id
        )
        
        result = {
            "scenario": scenario_name,
            "query": query,
            "response": response_text,
            "execution_time": execution_time,
            "tool_calls": tool_calls,
            "findings": findings,
            "session_state": {
                "discoveries": len(updated_session.state.get('discoveries', [])),
                "total_value": updated_session.state.get('total_value_found', 0),
                "patterns_used": updated_session.state.get('patterns_used', [])
            }
        }
        
        self.validation_results.append(result)
        return result
    
    def _extract_findings(self, response: str) -> Dict:
        """Extract financial values, equipment, and patterns from response.
        
        Args:
            response: Agent's response text
            
        Returns:
            Dict with extracted findings
        """
        findings = {
            "financial_values": [],
            "total_value": 0,
            "equipment": [],
            "products": [],
            "patterns": [],
            "recommendations": []
        }
        
        # Extract dollar values
        # Match patterns like $341K, $2.5M, $341,000, etc.
        dollar_patterns = [
            (r'\$([0-9,]+(?:\.[0-9]+)?)\s*[Mm](?:illion)?', 1_000_000),
            (r'\$([0-9,]+(?:\.[0-9]+)?)\s*[Kk]', 1_000),
            (r'\$([0-9,]+(?:\.[0-9]+)?)', 1)
        ]
        
        for pattern, multiplier in dollar_patterns:
            matches = re.finditer(pattern, response)
            for match in matches:
                value_str = match.group(1).replace(',', '')
                try:
                    value = float(value_str) * multiplier
                    findings["financial_values"].append({
                        "text": match.group(0),
                        "value": value
                    })
                    findings["total_value"] += value
                except ValueError:
                    pass
        
        # Extract equipment mentions (e.g., LINE2-PCK)
        equipment_pattern = r'LINE[0-9]-[A-Z]{3}'
        findings["equipment"] = list(set(re.findall(equipment_pattern, response)))
        
        # Extract product mentions
        products = ["Energy Drink", "Premium Juice", "Soda", "Kids Drink", "Sparkling Water"]
        for product in products:
            if product.lower() in response.lower():
                findings["products"].append(product)
        findings["products"] = list(set(findings["products"]))
        
        # Extract patterns and keywords
        pattern_keywords = [
            "micro-stop", "cascade", "cluster", "jam", "UNP-JAM",
            "night shift", "foaming", "scrap", "quality", "downtime",
            "10 minutes", "temporal", "pattern"
        ]
        
        for keyword in pattern_keywords:
            if keyword.lower() in response.lower():
                findings["patterns"].append(keyword)
        
        # Extract recommendations (lines starting with action words)
        recommendation_patterns = [
            r'(?:^|\n)\s*[-•]\s*([A-Z][^.!?]*(?:implement|fix|install|reduce|improve|focus)[^.!?]*[.!?])',
            r'(?:^|\n)\s*(?:Action|Recommendation):\s*([^.!?]+[.!?])'
        ]
        
        for pattern in recommendation_patterns:
            matches = re.finditer(pattern, response, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                findings["recommendations"].append(match.group(1).strip())
        
        return findings
    
    async def validate_all_scenarios(self) -> Dict:
        """Run all validation scenarios and generate summary report.
        
        Returns:
            Dict with validation summary and detailed results
        """
        await self.setup()
        
        # Define test scenarios based on manual prototype
        scenarios = [
            {
                "name": "hidden_capacity",
                "query": "Find equipment with significant capacity improvement opportunities. Focus on OEE gaps and calculate the financial impact."
            },
            {
                "name": "product_oee",
                "query": "Analyze product-specific OEE issues and their financial impact. Which products are causing the biggest losses?"
            },
            {
                "name": "temporal_patterns", 
                "query": "Find patterns in equipment failures and micro-stops. When do problems cluster and what's the cascade effect?"
            },
            {
                "name": "quality_tradeoff",
                "query": "Where are we losing money to quality issues and scrap? Calculate the ROI of quality improvements."
            },
            {
                "name": "comprehensive",
                "query": "Give me a comprehensive analysis of all improvement opportunities with total financial impact."
            }
        ]
        
        # Run each scenario
        for scenario in scenarios:
            await self.run_scenario(scenario["name"], scenario["query"])
            # Brief pause between scenarios
            await asyncio.sleep(2)
        
        # Generate validation report
        report = self._generate_validation_report()
        
        return report
    
    def _generate_validation_report(self) -> Dict:
        """Generate comprehensive validation report.
        
        Returns:
            Dict with validation summary and pass/fail status
        """
        # Calculate total value discovered across all scenarios
        total_value_found = sum(
            result["findings"]["total_value"] 
            for result in self.validation_results
        )
        
        # Check specific discoveries
        all_equipment = set()
        all_products = set()
        all_patterns = set()
        
        for result in self.validation_results:
            all_equipment.update(result["findings"]["equipment"])
            all_products.update(result["findings"]["products"])
            all_patterns.update(result["findings"]["patterns"])
        
        # Validation checks
        validations = {
            "total_value": {
                "found": total_value_found,
                "target": self.benchmarks["total_value"],
                "achievement_rate": (total_value_found / self.benchmarks["total_value"]) * 100,
                "passed": total_value_found >= self.benchmarks["total_value"] * 0.8  # 80% threshold
            },
            "hidden_capacity": {
                "equipment_found": "LINE2-PCK" in all_equipment,
                "keywords_found": any(
                    keyword in " ".join(all_patterns).lower() 
                    for keyword in self.benchmarks["hidden_capacity"]["root_cause"]
                ),
                "passed": "LINE2-PCK" in all_equipment
            },
            "product_oee": {
                "energy_drink_found": "Energy Drink" in all_products,
                "premium_juice_found": "Premium Juice" in all_products,
                "passed": "Energy Drink" in all_products or "Premium Juice" in all_products
            },
            "patterns": {
                "patterns_found": len(all_patterns),
                "key_patterns": [p for p in self.benchmarks["temporal_patterns"]["patterns"] if p in " ".join(all_patterns).lower()],
                "passed": len(all_patterns) >= 3
            }
        }
        
        # Overall pass/fail
        overall_passed = all(v.get("passed", False) for v in validations.values())
        
        # Performance metrics
        avg_execution_time = sum(r["execution_time"] for r in self.validation_results) / len(self.validation_results)
        total_tool_calls = sum(len(r["tool_calls"]) for r in self.validation_results)
        
        report = {
            "summary": {
                "overall_passed": overall_passed,
                "total_value_found": total_value_found,
                "achievement_rate": (total_value_found / self.benchmarks["total_value"]) * 100,
                "scenarios_run": len(self.validation_results),
                "avg_execution_time": avg_execution_time,
                "total_tool_calls": total_tool_calls
            },
            "validations": validations,
            "discoveries": {
                "equipment": list(all_equipment),
                "products": list(all_products),
                "patterns": list(all_patterns)
            },
            "detailed_results": self.validation_results,
            "timestamp": datetime.now().isoformat()
        }
        
        return report
    
    def save_report(self, report: Dict, filename: Optional[str] = None):
        """Save validation report to file.
        
        Args:
            report: Validation report dict
            filename: Optional filename (defaults to timestamped name)
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"validation_report_{timestamp}.json"
        
        filepath = f"adk_agents/tests/validation/{filename}"
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report saved to: {filepath}")
        
        # Also create a summary text file
        summary_path = filepath.replace('.json', '_summary.txt')
        with open(summary_path, 'w') as f:
            f.write("MANUAL PROTOTYPE VALIDATION SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Overall Status: {'PASSED' if report['summary']['overall_passed'] else 'FAILED'}\n")
            f.write(f"Achievement Rate: {report['summary']['achievement_rate']:.1f}%\n")
            f.write(f"Total Value Found: ${report['summary']['total_value_found']:,.0f}\n")
            f.write(f"Target Value: ${self.benchmarks['total_value']:,.0f}\n\n")
            
            f.write("Key Discoveries:\n")
            f.write(f"- Equipment: {', '.join(report['discoveries']['equipment'])}\n")
            f.write(f"- Products: {', '.join(report['discoveries']['products'])}\n")
            f.write(f"- Patterns: {len(report['discoveries']['patterns'])} found\n\n")
            
            f.write("Validation Results:\n")
            for key, val in report['validations'].items():
                f.write(f"- {key}: {'PASSED' if val.get('passed', False) else 'FAILED'}\n")
        
        logger.info(f"Summary saved to: {summary_path}")


async def main():
    """Run validation as standalone script."""
    validator = ManualPrototypeValidator()
    report = await validator.validate_all_scenarios()
    validator.save_report(report)
    
    # Print summary
    print("\nVALIDATION COMPLETE")
    print("=" * 50)
    print(f"Overall Status: {'PASSED' if report['summary']['overall_passed'] else 'FAILED'}")
    print(f"Achievement Rate: {report['summary']['achievement_rate']:.1f}%")
    print(f"Total Value Found: ${report['summary']['total_value_found']:,.0f}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())