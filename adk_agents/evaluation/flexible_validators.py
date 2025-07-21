"""
Flexible validators for manufacturing agent evaluation.

These validators check for insights similar to the manual prototype
without requiring exact matches or specific paths.
"""
import re
from typing import Dict, Any, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FlexibleValidator:
    """Validates agent findings against flexible criteria."""
    
    @staticmethod
    def validate_capacity_finding(
        response_text: str,
        tool_uses: List[Dict[str, Any]],
        criteria: Dict[str, Any]
    ) -> Tuple[float, Dict[str, bool]]:
        """
        Validate if agent found capacity opportunities.
        
        Returns:
            score: 0.0 to 1.0
            findings: dict of what was found
        """
        findings = {
            "found_low_oee": False,
            "calculated_gap": False,
            "quantified_roi": False
        }
        
        # Check for low OEE equipment (flexible patterns)
        oee_patterns = [
            r'(\d+\.?\d*)%?\s*(?:effective\s*)?OEE',
            r'OEE.*?(\d+\.?\d*)%',
            r'performance.*?(\d+\.?\d*)%'
        ]
        
        for pattern in oee_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            for match in matches:
                oee_value = float(match)
                if oee_value < criteria.get('threshold', 75.0):
                    findings["found_low_oee"] = True
                    break
        
        # Check for capacity gap calculation
        gap_patterns = [
            r'(\d+\.?\d*)%?\s*capacity\s*(?:gap|improvement|opportunity)',
            r'(?:gap|improvement).*?(\d+\.?\d*)%',
            r'(\d+\.?\d*)%?\s*(?:below|under)\s*(?:target|benchmark)'
        ]
        
        for pattern in gap_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            for match in matches:
                gap_value = float(match)
                if gap_value >= criteria.get('min_gap', 10.0):
                    findings["calculated_gap"] = True
                    break
        
        # Check for financial quantification
        roi_patterns = [
            r'\$(\d+)K',
            r'\$(\d+),?(\d+)',
            r'(\d+)K/year',
            r'(\d+)K\s*(?:annual|per\s*year)'
        ]
        
        min_roi = criteria.get('min_roi', 300000)
        max_roi = criteria.get('max_roi', 800000)
        
        for pattern in roi_patterns:
            matches = re.findall(pattern, response_text)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle comma-separated numbers
                    value = int(''.join(match)) 
                else:
                    # Handle K notation
                    value = int(match) * 1000
                    
                if min_roi <= value <= max_roi:
                    findings["quantified_roi"] = True
                    break
        
        # Calculate score based on partial credit
        partial_credit = criteria.get('partial_credit', {})
        score = 0.0
        
        if findings["found_low_oee"]:
            score += partial_credit.get('found_low_oee', 0.4)
        if findings["calculated_gap"]:
            score += partial_credit.get('calculated_gap', 0.3)
        if findings["quantified_roi"]:
            score += partial_credit.get('quantified_roi', 0.3)
            
        return score, findings
    
    @staticmethod
    def validate_pattern_finding(
        response_text: str,
        tool_uses: List[Dict[str, Any]],
        criteria: Dict[str, Any]
    ) -> Tuple[float, Dict[str, bool]]:
        """
        Validate if agent found temporal or shift patterns.
        
        Returns:
            score: 0.0 to 1.0
            findings: dict of what was found
        """
        findings = {
            "found_any_pattern": False,
            "identified_shift_differences": False,
            "quantified_impact": False
        }
        
        # Check for temporal patterns
        temporal_patterns = [
            r'within\s*(\d+)\s*minutes',
            r'(\d+)%\s*(?:of|chance).*?(?:jam|stop|downtime)',
            r'cluster.*?(\d+)',
            r'temporal\s*(?:pattern|clustering)',
            r'time-based\s*pattern'
        ]
        
        for pattern in temporal_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                findings["found_any_pattern"] = True
                break
        
        # Check for shift patterns
        shift_patterns = [
            r'night\s*shift.*?(\d+)%.*?(?:more|worse|higher)',
            r'shift.*?(?:variance|difference)',
            r'(?:day|night|evening)\s*shift.*?(?:better|worse|different)'
        ]
        
        for pattern in shift_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                findings["identified_shift_differences"] = True
                break
        
        # Check for financial impact (optional)
        if re.search(r'\$\d+K|\d+K/year', response_text):
            findings["quantified_impact"] = True
        
        # Calculate score
        partial_credit = criteria.get('partial_credit', {})
        score = 0.0
        
        if findings["found_any_pattern"]:
            score += partial_credit.get('found_any_pattern', 0.5)
        if findings["identified_shift_differences"]:
            score += partial_credit.get('identified_shift_differences', 0.3)
        if findings["quantified_impact"]:
            score += partial_credit.get('quantified_impact', 0.2)
            
        return score, findings
    
    @staticmethod
    def validate_quality_finding(
        response_text: str,
        tool_uses: List[Dict[str, Any]],
        criteria: Dict[str, Any]
    ) -> Tuple[float, Dict[str, bool]]:
        """
        Validate if agent found quality improvement opportunities.
        
        Returns:
            score: 0.0 to 1.0
            findings: dict of what was found
        """
        findings = {
            "identified_quality_gap": False,
            "calculated_scrap_cost": False,
            "provided_recommendations": False
        }
        
        # Check for quality gap
        quality_patterns = [
            r'(\d+\.?\d*)%?\s*(?:quality|scrap)',
            r'quality.*?(\d+\.?\d*)%',
            r'(\d+)%\s*(?:vs|versus|compared to).*?target'
        ]
        
        for pattern in quality_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            for match in matches:
                quality_value = float(match)
                # Check if quality is below 98% or scrap is above 2%
                if quality_value < 98 or (quality_value < 10 and 'scrap' in response_text.lower()):
                    findings["identified_quality_gap"] = True
                    break
        
        # Check for scrap cost calculation
        cost_patterns = [
            r'\$(\d+)K.*?scrap',
            r'scrap.*?\$(\d+)K',
            r'(\d+)K.*?annual.*?(?:scrap|quality)',
            r'quality.*?cost.*?\$(\d+)'
        ]
        
        min_cost = criteria.get('min_annual_cost', 100000)
        
        for pattern in cost_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            for match in matches:
                value = int(match) * 1000 if 'K' in pattern else int(match)
                if value >= min_cost:
                    findings["calculated_scrap_cost"] = True
                    break
        
        # Check for recommendations
        recommendation_keywords = ["roi", "investment", "action", "recommendation", "improve", "reduce"]
        keyword_count = sum(1 for keyword in recommendation_keywords if keyword in response_text.lower())
        
        if keyword_count >= 3:
            findings["provided_recommendations"] = True
        
        # Calculate score
        partial_credit = criteria.get('partial_credit', {})
        score = 0.0
        
        if findings["identified_quality_gap"]:
            score += partial_credit.get('identified_quality_gap', 0.3)
        if findings["calculated_scrap_cost"]:
            score += partial_credit.get('calculated_scrap_cost', 0.4)
        if findings["provided_recommendations"]:
            score += partial_credit.get('provided_recommendations', 0.3)
            
        return score, findings


    @staticmethod
    def validate_target_findings(
        response_text: str,
        tool_uses: List[Dict[str, Any]],
        target_findings: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Validate if agent found insights similar to manual prototype targets.
        
        Args:
            response_text: Agent's response
            tool_uses: Tools used by agent
            target_findings: Expected findings from manual prototype
            
        Returns:
            score: 0.0 to 1.0
            details: Dictionary with validation details
        """
        findings = {
            "found_insights": [],
            "total_value_found": 0,
            "within_target_range": False,
            "key_insights_covered": 0
        }
        
        # Extract all monetary values from response
        money_patterns = [
            r'\$(\d+)K',
            r'\$(\d+),?(\d+)',
            r'\$(\d+\.?\d*)M',
            r'(\d+)K/year',
            r'(\d+)K\s*(?:annual|per\s*year)'
        ]
        
        found_values = []
        for pattern in money_patterns:
            matches = re.findall(pattern, response_text)
            for match in matches:
                if isinstance(match, tuple):
                    value = int(''.join(match))
                elif 'M' in pattern:
                    value = int(float(match) * 1000000)
                else:
                    value = int(match) * 1000 if 'K' in pattern else int(match)
                found_values.append(value)
                findings["found_insights"].append(f"${value:,}")
        
        # Calculate total value found
        if found_values:
            findings["total_value_found"] = sum(found_values)
            
            # Check if within expected magnitude
            expected_mag = target_findings.get("expected_magnitude", {})
            if "min_annual_value" in expected_mag and "max_annual_value" in expected_mag:
                # For individual opportunities
                for value in found_values:
                    if expected_mag["min_annual_value"] <= value <= expected_mag["max_annual_value"]:
                        findings["within_target_range"] = True
                        break
            elif "min_total_value" in expected_mag and "max_total_value" in expected_mag:
                # For total opportunities
                total = findings["total_value_found"]
                if expected_mag["min_total_value"] <= total <= expected_mag["max_total_value"]:
                    findings["within_target_range"] = True
        
        # Check key insights coverage
        key_insights = target_findings.get("key_insights", [])
        for insight in key_insights:
            # Flexible pattern matching for key concepts
            insight_lower = insight.lower()
            if any(keyword in response_text.lower() for keyword in insight_lower.split()):
                findings["key_insights_covered"] += 1
        
        # Calculate score
        score = 0.0
        
        # Value discovery (40%)
        if findings["total_value_found"] > 0:
            score += 0.2
            if findings["within_target_range"]:
                score += 0.2
        
        # Key insights coverage (60%)
        if key_insights:
            insight_ratio = findings["key_insights_covered"] / len(key_insights)
            score += insight_ratio * 0.6
        else:
            # If no key insights specified, give full credit if value found
            if findings["total_value_found"] > 0:
                score += 0.6
        
        return score, findings


def validate_response(
    validation_type: str,
    response_text: str,
    tool_uses: List[Dict[str, Any]],
    criteria: Dict[str, Any]
) -> Tuple[float, Dict[str, Any]]:
    """
    Main validation function that routes to specific validators.
    
    Args:
        validation_type: Type of validation (capacity_analysis, pattern_analysis, quality_analysis)
        response_text: Agent's response text
        tool_uses: List of tools used by agent
        criteria: Validation criteria
        
    Returns:
        score: 0.0 to 1.0
        details: Dictionary with findings and debug info
    """
    validator = FlexibleValidator()
    
    if validation_type == "capacity_analysis":
        score, findings = validator.validate_capacity_finding(response_text, tool_uses, criteria)
    elif validation_type == "pattern_analysis":
        score, findings = validator.validate_pattern_finding(response_text, tool_uses, criteria)
    elif validation_type == "quality_analysis":
        score, findings = validator.validate_quality_finding(response_text, tool_uses, criteria)
    else:
        logger.warning(f"Unknown validation type: {validation_type}")
        score, findings = 0.0, {}
    
    return score, {
        "validation_type": validation_type,
        "findings": findings,
        "score": score,
        "passed": score >= 0.7  # 70% threshold for passing
    }


def validate_target_based_response(
    response_text: str,
    tool_uses: List[Dict[str, Any]],
    target_findings: Dict[str, Any]
) -> Tuple[float, Dict[str, Any]]:
    """
    Validate response against manual prototype target findings.
    
    Args:
        response_text: Agent's response
        tool_uses: Tools used by agent
        target_findings: Expected findings from manual prototype
        
    Returns:
        score: 0.0 to 1.0
        details: Dictionary with validation details
    """
    validator = FlexibleValidator()
    score, findings = validator.validate_target_findings(response_text, tool_uses, target_findings)
    
    return score, {
        "target_validation": True,
        "expected_reference": target_findings.get("reference", ""),
        "findings": findings,
        "score": score,
        "passed": score >= 0.6  # 60% threshold for target-based validation
    }