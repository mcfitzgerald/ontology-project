"""Outcome evaluator for extracting and validating financial discoveries.

This module provides sophisticated extraction and evaluation of agent responses
to determine if key discoveries match manual prototype benchmarks.
"""
import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class OutcomeEvaluator:
    """Evaluates agent outcomes against manual prototype benchmarks."""
    
    def __init__(self):
        """Initialize evaluator with extraction patterns."""
        # Financial value patterns
        self.value_patterns = [
            # $2.5M, $2.5 million
            (r'\$([0-9]+(?:\.[0-9]+)?)\s*[Mm](?:illion)?', 1_000_000),
            # $341K, $341k
            (r'\$([0-9]+(?:\.[0-9]+)?)\s*[Kk]', 1_000),
            # $341,000 or $341000
            (r'\$([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)', 1),
            # "worth $X" or "value of $X"
            (r'(?:worth|value of|impact of|save|gain|opportunity)\s*(?:of\s*)?\$([0-9,]+(?:\.[0-9]+)?)', 1),
            # "$X per year" or "$X/year"
            (r'\$([0-9,]+(?:\.[0-9]+)?)\s*(?:per year|\/year|annually)', 1),
        ]
        
        # Equipment and product patterns
        self.equipment_pattern = r'LINE[0-9]-[A-Z]{3}'
        self.products = [
            "Energy Drink", "Premium Juice", "Soda", 
            "Kids Drink", "Sparkling Water", "12oz Soda",
            "16oz Energy Drink", "32oz Premium Juice"
        ]
        
        # Key insight patterns
        self.insight_patterns = {
            "percentage": r'(\d+(?:\.\d+)?)\s*%',
            "time_value": r'(\d+(?:\.\d+)?)\s*(?:hours?|minutes?|days?)',
            "unit_count": r'(\d{1,3}(?:,\d{3})*)\s*(?:units?|products?)',
            "frequency": r'(\d+(?:\.\d+)?)\s*(?:times?|occurrences?|events?)'
        }
    
    def extract_financial_impact(self, text: str) -> Dict[str, any]:
        """Extract all financial values and calculate total impact.
        
        Args:
            text: Agent response text
            
        Returns:
            Dict with financial findings including total value
        """
        findings = {
            "values": [],
            "total": 0,
            "confidence": "low",
            "value_contexts": []
        }
        
        # Extract all monetary values with context
        for pattern, multiplier in self.value_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                try:
                    # Get surrounding context (50 chars before and after)
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].strip()
                    
                    # Extract and calculate value
                    value_str = match.group(1).replace(',', '')
                    value = float(value_str) * multiplier
                    
                    findings["values"].append({
                        "raw": match.group(0),
                        "value": value,
                        "context": context
                    })
                    
                except (ValueError, IndexError):
                    continue
        
        # Calculate total, avoiding duplicates
        if findings["values"]:
            # Sort by value descending
            findings["values"].sort(key=lambda x: x["value"], reverse=True)
            
            # Simple deduplication - if values are within 10% of each other, consider them duplicates
            unique_values = []
            for val in findings["values"]:
                is_duplicate = False
                for unique in unique_values:
                    if abs(val["value"] - unique["value"]) / max(val["value"], unique["value"]) < 0.1:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_values.append(val)
            
            findings["values"] = unique_values
            findings["total"] = sum(v["value"] for v in unique_values)
            
            # Set confidence based on value count and clarity
            if len(unique_values) >= 3:
                findings["confidence"] = "high"
            elif len(unique_values) >= 1:
                findings["confidence"] = "medium"
        
        return findings
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract equipment, products, and other key entities.
        
        Args:
            text: Agent response text
            
        Returns:
            Dict with categorized entities
        """
        entities = {
            "equipment": [],
            "products": [],
            "issues": [],
            "time_patterns": []
        }
        
        # Extract equipment
        equipment_matches = re.findall(self.equipment_pattern, text)
        entities["equipment"] = list(set(equipment_matches))
        
        # Extract products (case-insensitive)
        text_lower = text.lower()
        for product in self.products:
            if product.lower() in text_lower:
                entities["products"].append(product)
        entities["products"] = list(set(entities["products"]))
        
        # Extract key issues
        issue_keywords = [
            "jam", "micro-stop", "microstop", "UNP-JAM", "foaming",
            "scrap", "quality", "downtime", "failure", "bottleneck"
        ]
        for issue in issue_keywords:
            if issue.lower() in text_lower:
                entities["issues"].append(issue)
        
        # Extract time patterns
        time_patterns = [
            "night shift", "day shift", "morning", "afternoon",
            "10 minutes", "within minutes", "cascade", "cluster"
        ]
        for pattern in time_patterns:
            if pattern.lower() in text_lower:
                entities["time_patterns"].append(pattern)
        
        return entities
    
    def extract_insights(self, text: str) -> List[Dict[str, str]]:
        """Extract key insights and findings from text.
        
        Args:
            text: Agent response text
            
        Returns:
            List of insight dictionaries
        """
        insights = []
        
        # Look for specific insight patterns
        insight_indicators = [
            r"(?:found|discovered|identified|detected)\s+(.+?)(?:\.|,|\n)",
            r"(?:key finding|insight|opportunity):\s*(.+?)(?:\.|,|\n)",
            r"(?:analysis reveals|data shows|results indicate)\s+(.+?)(?:\.|,|\n)",
            r"(?:root cause|main issue|primary problem):\s*(.+?)(?:\.|,|\n)"
        ]
        
        for pattern in insight_indicators:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                insight_text = match.group(1).strip()
                
                # Extract any percentages in the insight
                percentages = re.findall(r'(\d+(?:\.\d+)?)\s*%', insight_text)
                
                # Extract any financial values
                values = []
                for val_pattern, multiplier in self.value_patterns[:3]:
                    val_matches = re.findall(val_pattern, insight_text)
                    values.extend(val_matches)
                
                insights.append({
                    "text": insight_text,
                    "percentages": percentages,
                    "has_financial": len(values) > 0,
                    "type": self._classify_insight(insight_text)
                })
        
        return insights
    
    def _classify_insight(self, insight_text: str) -> str:
        """Classify the type of insight.
        
        Args:
            insight_text: The insight text to classify
            
        Returns:
            Classification string
        """
        text_lower = insight_text.lower()
        
        if any(word in text_lower for word in ["capacity", "oee", "performance"]):
            return "capacity"
        elif any(word in text_lower for word in ["quality", "scrap", "defect"]):
            return "quality"
        elif any(word in text_lower for word in ["pattern", "cluster", "trend"]):
            return "pattern"
        elif any(word in text_lower for word in ["product", "sku", "item"]):
            return "product"
        else:
            return "general"
    
    def evaluate_response(self, response: str, expected: Dict) -> Dict[str, any]:
        """Evaluate if response meets expected criteria.
        
        Args:
            response: Agent response text
            expected: Expected discoveries from scenario
            
        Returns:
            Evaluation results with pass/fail status
        """
        # Extract all components
        financial = self.extract_financial_impact(response)
        entities = self.extract_entities(response)
        insights = self.extract_insights(response)
        
        evaluation = {
            "extracted": {
                "financial": financial,
                "entities": entities,
                "insights": insights
            },
            "checks": {},
            "passed": False
        }
        
        # Check financial value if expected
        if "value_range" in expected:
            min_val, max_val = expected["value_range"]
            value_found = financial["total"]
            evaluation["checks"]["financial_range"] = {
                "expected": f"${min_val:,} - ${max_val:,}",
                "found": f"${value_found:,}",
                "passed": min_val <= value_found <= max_val * 1.5  # Allow some overachievement
            }
        
        if "total_value" in expected:
            target = expected["total_value"]
            value_found = financial["total"]
            evaluation["checks"]["financial_target"] = {
                "expected": f"${target:,}",
                "found": f"${value_found:,}",
                "passed": value_found >= target * 0.8  # 80% threshold
            }
        
        # Check entity discovery
        if "equipment" in expected:
            found_equipment = set(entities["equipment"])
            expected_equipment = set(expected["equipment"])
            evaluation["checks"]["equipment"] = {
                "expected": expected["equipment"],
                "found": entities["equipment"],
                "passed": bool(expected_equipment & found_equipment)
            }
        
        if "products" in expected:
            found_products = set(entities["products"])
            expected_products = set(expected["products"])
            evaluation["checks"]["products"] = {
                "expected": expected["products"],
                "found": entities["products"],
                "passed": bool(expected_products & found_products)
            }
        
        # Check keyword presence
        if "keywords" in expected:
            response_lower = response.lower()
            keywords_found = [kw for kw in expected["keywords"] if kw.lower() in response_lower]
            evaluation["checks"]["keywords"] = {
                "expected": len(expected["keywords"]),
                "found": len(keywords_found),
                "keywords": keywords_found,
                "passed": len(keywords_found) >= len(expected["keywords"]) * 0.5  # 50% threshold
            }
        
        # Overall pass determination
        check_results = [check["passed"] for check in evaluation["checks"].values()]
        evaluation["passed"] = all(check_results) if check_results else False
        
        return evaluation
    
    def calculate_achievement_score(self, results: List[Dict]) -> float:
        """Calculate overall achievement score from multiple evaluations.
        
        Args:
            results: List of evaluation results
            
        Returns:
            Achievement score (0-100)
        """
        if not results:
            return 0.0
        
        # Weight different aspects
        weights = {
            "financial": 0.4,
            "entities": 0.3,
            "insights": 0.2,
            "coverage": 0.1
        }
        
        scores = {
            "financial": 0,
            "entities": 0,
            "insights": 0,
            "coverage": 0
        }
        
        # Calculate financial score (based on total value found)
        total_value = sum(
            r["extracted"]["financial"]["total"] 
            for r in results
        )
        # Target is $2.5M from manual prototype
        scores["financial"] = min(100, (total_value / 2_500_000) * 100)
        
        # Calculate entity discovery score
        all_equipment = set()
        all_products = set()
        for r in results:
            all_equipment.update(r["extracted"]["entities"]["equipment"])
            all_products.update(r["extracted"]["entities"]["products"])
        
        # Key entities from manual prototype
        key_equipment = {"LINE2-PCK", "LINE3-FIL", "LINE1"}
        key_products = {"Energy Drink", "Premium Juice"}
        
        equipment_score = len(all_equipment & key_equipment) / len(key_equipment) * 100
        product_score = len(all_products & key_products) / len(key_products) * 100
        scores["entities"] = (equipment_score + product_score) / 2
        
        # Calculate insight quality score
        total_insights = sum(len(r["extracted"]["insights"]) for r in results)
        financial_insights = sum(
            1 for r in results 
            for i in r["extracted"]["insights"] 
            if i["has_financial"]
        )
        scores["insights"] = min(100, (total_insights * 10) + (financial_insights * 20))
        
        # Calculate coverage score (how many scenarios passed)
        passed_scenarios = sum(1 for r in results if r.get("passed", False))
        scores["coverage"] = (passed_scenarios / len(results)) * 100 if results else 0
        
        # Calculate weighted total
        total_score = sum(scores[k] * weights[k] for k in weights)
        
        return round(total_score, 1)