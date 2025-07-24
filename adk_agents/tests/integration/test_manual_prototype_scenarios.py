"""Integration tests for manual prototype scenarios.

These tests run the ADK agent through key scenarios from the manual prototype
and verify that comparable discoveries are made.
"""
import pytest
import asyncio
from typing import Dict

from adk_agents.tests.validation.manual_prototype_validator import ManualPrototypeValidator
from adk_agents.tests.validation.outcome_evaluator import OutcomeEvaluator
from adk_agents.tests.validation.scenario_definitions import VALIDATION_SCENARIOS, TEST_CASES


class TestManualPrototypeScenarios:
    """Test suite for validating agent against manual prototype."""
    
    @pytest.fixture
    async def validator(self):
        """Create and setup validator instance."""
        validator = ManualPrototypeValidator()
        await validator.setup()
        return validator
    
    @pytest.fixture
    def evaluator(self):
        """Create outcome evaluator instance."""
        return OutcomeEvaluator()
    
    @pytest.mark.asyncio
    async def test_hidden_capacity_discovery(self, validator, evaluator):
        """Test discovery of LINE2-PCK hidden capacity opportunity."""
        scenario = VALIDATION_SCENARIOS["hidden_capacity"]
        
        # Run the scenario
        result = await validator.run_scenario(
            "hidden_capacity",
            scenario["queries"][0]
        )
        
        # Evaluate the response
        evaluation = evaluator.evaluate_response(
            result["response"],
            scenario["expected_discoveries"]
        )
        
        # Assertions
        assert evaluation["passed"], f"Hidden capacity scenario failed: {evaluation['checks']}"
        
        # Specific checks
        assert "LINE2-PCK" in evaluation["extracted"]["entities"]["equipment"], \
            "Failed to identify LINE2-PCK as problem equipment"
        
        financial = evaluation["extracted"]["financial"]["total"]
        assert financial >= 341_000, \
            f"Financial impact ${financial:,} below minimum $341,000"
        
        # Check for key insights
        keywords = ["jam", "micro-stop", "downtime"]
        response_lower = result["response"].lower()
        found_keywords = [kw for kw in keywords if kw in response_lower]
        assert len(found_keywords) >= 2, \
            f"Missing key insights. Found only: {found_keywords}"
    
    @pytest.mark.asyncio
    async def test_product_oee_issues(self, validator, evaluator):
        """Test discovery of product-specific OEE problems."""
        scenario = VALIDATION_SCENARIOS["product_oee"]
        
        # Run the scenario
        result = await validator.run_scenario(
            "product_oee",
            scenario["queries"][0]
        )
        
        # Evaluate the response
        evaluation = evaluator.evaluate_response(
            result["response"],
            scenario["expected_discoveries"]
        )
        
        # Check product identification
        products = evaluation["extracted"]["entities"]["products"]
        assert "Energy Drink" in products or "Premium Juice" in products, \
            f"Failed to identify key problem products. Found: {products}"
        
        # Check financial impact
        financial = evaluation["extracted"]["financial"]["total"]
        assert financial >= 500_000, \
            f"Financial impact ${financial:,} below expected for product issues"
        
        # Check for specific issues
        issues = evaluation["extracted"]["entities"]["issues"]
        assert any(issue in ["foaming", "scrap", "quality"] for issue in issues), \
            f"Failed to identify specific product issues. Found: {issues}"
    
    @pytest.mark.asyncio
    async def test_temporal_pattern_recognition(self, validator, evaluator):
        """Test discovery of micro-stop patterns and clustering."""
        scenario = VALIDATION_SCENARIOS["temporal_patterns"]
        
        # Run the scenario
        result = await validator.run_scenario(
            "temporal_patterns",
            scenario["queries"][0]
        )
        
        # Check for pattern keywords
        response_lower = result["response"].lower()
        pattern_keywords = ["cluster", "cascade", "pattern", "10 minutes", "night shift"]
        found_patterns = [kw for kw in pattern_keywords if kw in response_lower]
        
        assert len(found_patterns) >= 2, \
            f"Failed to identify temporal patterns. Found only: {found_patterns}"
        
        # Check for quantification
        evaluation = evaluator.evaluate_response(
            result["response"],
            scenario["expected_discoveries"]
        )
        
        financial = evaluation["extracted"]["financial"]["total"]
        assert financial >= 200_000, \
            f"Pattern prevention value ${financial:,} below expected $200K+"
    
    @pytest.mark.asyncio
    async def test_quality_tradeoff_analysis(self, validator, evaluator):
        """Test quality-cost trade-off discovery."""
        scenario = VALIDATION_SCENARIOS["quality_tradeoff"]
        
        # Run the scenario
        result = await validator.run_scenario(
            "quality_tradeoff",
            scenario["queries"][0]
        )
        
        # Check for quality/scrap analysis
        response_lower = result["response"].lower()
        quality_keywords = ["scrap", "quality", "roi", "inspection"]
        found_keywords = [kw for kw in quality_keywords if kw in response_lower]
        
        assert len(found_keywords) >= 2, \
            f"Failed to analyze quality trade-offs. Found only: {found_keywords}"
        
        # Check for recommendations
        assert "recommendation" in response_lower or "improve" in response_lower, \
            "Failed to provide quality improvement recommendations"
    
    @pytest.mark.asyncio
    async def test_comprehensive_value_discovery(self, validator, evaluator):
        """Test total value discovery across all opportunities."""
        # Run comprehensive analysis
        result = await validator.run_scenario(
            "comprehensive",
            VALIDATION_SCENARIOS["comprehensive"]["queries"][0]
        )
        
        # Extract total financial impact
        evaluation = evaluator.evaluate_response(
            result["response"],
            VALIDATION_SCENARIOS["comprehensive"]["expected_discoveries"]
        )
        
        total_value = evaluation["extracted"]["financial"]["total"]
        target_value = 2_500_000
        achievement_rate = (total_value / target_value) * 100
        
        assert total_value >= 2_000_000, \
            f"Total value ${total_value:,} below 80% of target ${target_value:,} (achievement: {achievement_rate:.1f}%)"
        
        # Check for key discoveries
        entities = evaluation["extracted"]["entities"]
        assert "LINE2-PCK" in entities["equipment"], \
            "Comprehensive analysis missed LINE2-PCK"
        
        key_products = {"Energy Drink", "Premium Juice"}
        found_products = set(entities["products"]) & key_products
        assert len(found_products) >= 1, \
            f"Comprehensive analysis missed key products. Found: {entities['products']}"
    
    @pytest.mark.asyncio
    async def test_specific_line2_pck_case(self, validator, evaluator):
        """Test specific discovery of LINE2-PCK issue from manual prototype."""
        test_case = TEST_CASES["line2_pck_discovery"]
        
        # Run specific query
        result = await validator.run_scenario(
            "line2_pck_specific",
            test_case["query"]
        )
        
        # Verify specific requirements
        response = result["response"]
        assert test_case["must_find"]["equipment"] in response, \
            f"Failed to identify {test_case['must_find']['equipment']}"
        
        # Extract and verify financial impact
        evaluation = evaluator.evaluate_response(response, test_case["must_find"])
        financial = evaluation["extracted"]["financial"]["total"]
        
        assert financial >= test_case["must_find"]["min_value"], \
            f"LINE2-PCK value ${financial:,} below required ${test_case['must_find']['min_value']:,}"
    
    @pytest.mark.asyncio
    async def test_discovery_progression(self, validator):
        """Test that discoveries build on each other across queries."""
        # Run multiple queries in sequence
        queries = [
            "Show me equipment with OEE below 85%",
            "What's causing the performance issues on LINE2-PCK?",
            "Calculate the financial impact of fixing these issues"
        ]
        
        cumulative_value = 0
        discoveries = []
        
        for i, query in enumerate(queries):
            result = await validator.run_scenario(f"progression_{i}", query)
            
            # Check that state is building
            assert result["session_state"]["discoveries"] >= i, \
                f"Discovery count not increasing: {result['session_state']['discoveries']}"
            
            # Track cumulative value
            if result["session_state"]["total_value"] > cumulative_value:
                cumulative_value = result["session_state"]["total_value"]
            
            discoveries.extend(result["findings"]["equipment"])
        
        # Verify progression led to valuable discoveries
        assert cumulative_value >= 300_000, \
            f"Progressive discovery value ${cumulative_value:,} too low"
        
        assert "LINE2-PCK" in discoveries, \
            "Failed to discover LINE2-PCK through progression"


# Standalone test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])