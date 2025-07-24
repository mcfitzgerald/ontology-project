"""Test scenario definitions based on manual prototype discoveries.

These scenarios represent the key business questions and expected discoveries
from the manual prototype that found $2.5M+ in opportunities.
"""

# Scenarios directly from Reference/manual_prototype.md
VALIDATION_SCENARIOS = {
    "hidden_capacity": {
        "name": "Hidden Capacity Analysis",
        "description": "Find equipment performance gaps like LINE2-PCK micro-stops",
        "queries": [
            "Find equipment with significant capacity improvement opportunities. Focus on OEE gaps and calculate the financial impact.",
            "What's the hidden production capacity if we solve our biggest OEE bottlenecks?",
            "Show me equipment running below 85% OEE and quantify the improvement opportunity."
        ],
        "expected_discoveries": {
            "equipment": ["LINE2-PCK"],
            "value_range": (341_000, 700_000),
            "keywords": ["micro-stop", "jam", "UNP-JAM", "downtime", "25%"],
            "insights": [
                "LINE2-PCK has chronic jamming issues",
                "81.5 hours of downtime",
                "342,650 units lost production"
            ]
        },
        "manual_prototype_finding": "$341K-$700K/year from fixing LINE2-PCK micro-stops"
    },
    
    "product_oee": {
        "name": "Product-Specific OEE Analysis", 
        "description": "Identify products causing performance issues",
        "queries": [
            "Analyze product-specific OEE issues and their financial impact. Which products are causing the biggest losses?",
            "Which products are killing our OEE and why? Focus on financial impact.",
            "Show me OEE by product and identify the worst performers with root causes."
        ],
        "expected_discoveries": {
            "products": ["Energy Drink", "Premium Juice"],
            "total_value": 806_000,
            "specific_issues": {
                "Energy Drink": {
                    "value": 710_000,
                    "issue": "foaming",
                    "impact": "15% speed reduction"
                },
                "Premium Juice": {
                    "value": 97_000,
                    "issue": "scrap",
                    "impact": "3% scrap vs 1% target"
                }
            },
            "keywords": ["foaming", "scrap", "quality", "speed reduction"]
        },
        "manual_prototype_finding": "$806K/year from product-specific issues"
    },
    
    "temporal_patterns": {
        "name": "Micro-Stop Pattern Recognition",
        "description": "Find when and why problems cluster",
        "queries": [
            "Find patterns in equipment failures and micro-stops. When do problems cluster and what's the cascade effect?",
            "When and why do micro-stops cluster, and what's the cascade effect?",
            "Analyze temporal patterns in downtime events. Are there predictable triggers?"
        ],
        "expected_discoveries": {
            "value_range": (250_000, 350_000),
            "patterns": [
                "60% of jams occur within 10 minutes",
                "Night shift 40% worse",
                "Cascade effect",
                "Clustering pattern"
            ],
            "keywords": ["cascade", "cluster", "10 minutes", "night shift", "pattern"],
            "prevention_opportunity": "50% prevention = 228 hours saved"
        },
        "manual_prototype_finding": "$250K-$350K from pattern-based prevention"
    },
    
    "quality_tradeoff": {
        "name": "Quality-Cost Trade-off Analysis",
        "description": "Balance quality improvements with costs",
        "queries": [
            "Where are we losing money to quality issues and scrap? Calculate the ROI of quality improvements.",
            "Where's the sweet spot between quality and cost?",
            "Analyze scrap rates by product and calculate the improvement opportunity."
        ],
        "expected_discoveries": {
            "total_scrap_cost": 200_000,
            "improvement_potential": 144_000,
            "keywords": ["scrap", "quality", "margin", "ROI"],
            "recommendations": [
                "Enhanced inspection for high-margin products",
                "Focus on Premium Juice and Energy Drink",
                "3-4 month payback on inspection upgrade"
            ]
        },
        "manual_prototype_finding": "$200K/year in scrap reduction opportunities"
    },
    
    "comprehensive": {
        "name": "Comprehensive Opportunity Analysis",
        "description": "Full discovery of all improvement opportunities",
        "queries": [
            "Give me a comprehensive analysis of all improvement opportunities with total financial impact.",
            "What's the total value of all optimization opportunities across equipment, products, and quality?",
            "Summarize all discovered improvement opportunities with prioritized recommendations."
        ],
        "expected_discoveries": {
            "total_value_min": 2_000_000,  # 80% of $2.5M target
            "categories": ["hidden capacity", "product issues", "quality", "patterns"],
            "top_opportunities": [
                "LINE2-PCK micro-stops",
                "Energy Drink foaming", 
                "Premium Juice scrap",
                "Night shift patterns"
            ]
        },
        "manual_prototype_finding": "$2.5M+ total annual opportunity"
    }
}

# Specific test cases for integration tests
TEST_CASES = {
    "line2_pck_discovery": {
        "query": "Which equipment has the biggest gap between current and world-class OEE?",
        "must_find": {
            "equipment": "LINE2-PCK",
            "min_value": 300_000,
            "keywords": ["jam", "micro-stop"]
        }
    },
    
    "energy_drink_issue": {
        "query": "Why is Energy Drink performing poorly and what's the financial impact?",
        "must_find": {
            "product": "Energy Drink",
            "min_value": 500_000,
            "keywords": ["foaming", "speed"]
        }
    },
    
    "night_shift_pattern": {
        "query": "Are there shift-based patterns in equipment failures?",
        "must_find": {
            "keywords": ["night shift", "40%", "pattern"],
            "min_value": 200_000
        }
    },
    
    "scrap_analysis": {
        "query": "Calculate annual scrap costs by product and improvement potential.",
        "must_find": {
            "min_value": 150_000,
            "keywords": ["scrap", "quality", "Premium Juice"]
        }
    }
}

# Validation thresholds
VALIDATION_CRITERIA = {
    "financial_discovery_rate": 0.8,  # Must find 80% of manual prototype value
    "entity_recognition_rate": 0.9,   # Must identify 90% of key entities
    "pattern_detection_minimum": 3,    # Must find at least 3 pattern types
    "recommendation_quality": {
        "must_include_roi": True,
        "must_be_actionable": True,
        "must_prioritize": True
    }
}