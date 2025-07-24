"""Guided discovery scenarios that mimic how the manual prototype was conducted.

Each scenario is a multi-step conversation that progressively guides the agent
toward specific discoveries through targeted questions.
"""

GUIDED_SCENARIOS = {
    "line2_pck_deep_dive": {
        "name": "LINE2-PCK Micro-Stop Investigation",
        "description": "Progressive discovery of LINE2-PCK issues matching manual prototype",
        "steps": [
            {
                "prompt": "Find all equipment and their average OEE. Which ones are below the 85% world-class benchmark?",
                "validate": ["LINE2-PCK", "OEE", "72"],
                "stop_if_not_found": False  # Continue even if some validations fail
            },
            {
                "prompt": "For LINE2-PCK specifically, calculate the financial impact of improving its OEE to 85%. What's the annual opportunity?",
                "validate": ["$300000", "$400000", "$500000", "$600000", "$700000"],
                "expected_range": (300000, 700000)
            },
            {
                "prompt": "Now analyze the downtime events for LINE2-PCK. What are the main reasons for downtime? Look for patterns in the reasons.",
                "validate": ["jam", "UNP-JAM", "material jam", "downtime"],
                "concepts": ["root_cause_analysis"]
            },
            {
                "prompt": "For LINE2-PCK's jam issues, are there any temporal patterns? Do these jams cluster at certain times or happen more during specific shifts?",
                "validate": ["cluster", "night shift", "temporal", "pattern", "10 minutes", "shift"],
                "concepts": ["temporal_analysis", "shift_patterns"]
            },
            {
                "prompt": "Quantify the total downtime hours and lost production units from LINE2-PCK jams. What's the total impact?",
                "validate": ["hours", "units", "production loss", "81", "82", "342"],
                "expected_findings": ["81.5 hours", "342,650 units"]
            }
        ],
        "expected_total_value": 341000  # Minimum expected
    },
    
    "product_performance_analysis": {
        "name": "Product-Specific OEE Investigation", 
        "description": "Discover product-related performance issues",
        "steps": [
            {
                "prompt": "List all products in the system with their basic information like target rates and prices.",
                "validate": ["Energy Drink", "Premium Juice", "SKU"],
                "concepts": ["product_discovery"]
            },
            {
                "prompt": "Analyze OEE by product. Which products have the worst performance and why? Focus on Energy Drink and Premium Juice if they appear.",
                "validate": ["Energy Drink", "Premium Juice", "OEE", "performance"],
                "stop_if_not_found": False
            },
            {
                "prompt": "For Energy Drink (16oz), are there any specific production issues? Check for speed reductions or quality problems.",
                "validate": ["foam", "speed", "reduction", "15%", "Energy Drink"],
                "concepts": ["product_specific_issues"]
            },
            {
                "prompt": "What's the financial impact of Energy Drink's production issues? Calculate the annual loss from reduced speed.",
                "validate": ["$500000", "$600000", "$700000", "$800000"],
                "expected_range": (500000, 800000)
            },
            {
                "prompt": "For Premium Juice (32oz), analyze the quality metrics and scrap rates. What's the financial impact of quality issues?",
                "validate": ["scrap", "quality", "3%", "Premium Juice"],
                "concepts": ["quality_analysis"]
            }
        ],
        "expected_total_value": 806000
    },
    
    "temporal_pattern_discovery": {
        "name": "Temporal and Cascade Pattern Analysis",
        "description": "Discover time-based patterns and equipment interactions",
        "steps": [
            {
                "prompt": "Analyze downtime events across all equipment. Are there any temporal patterns or clusters?",
                "validate": ["pattern", "cluster", "temporal", "time"],
                "concepts": ["pattern_recognition"]
            },
            {
                "prompt": "Focus on micro-stops (events under 10 minutes). Do they tend to occur in clusters? What percentage happen within 10 minutes of each other?",
                "validate": ["micro-stop", "10 minutes", "cluster", "60%", "percent"],
                "expected_findings": ["60% within 10 minutes"]
            },
            {
                "prompt": "Compare equipment performance by shift. Is there a significant difference between day and night shift performance?",
                "validate": ["night shift", "day shift", "40%", "worse", "shift"],
                "concepts": ["shift_analysis"]
            },
            {
                "prompt": "When LINE2-PCK has issues, what's the impact on downstream equipment like LINE2-PAL? Is there a cascade effect?",
                "validate": ["cascade", "downstream", "LINE2-PAL", "impact"],
                "concepts": ["cascade_analysis"]
            },
            {
                "prompt": "If we could prevent 50% of these clustered micro-stops through predictive intervention, what would be the financial benefit?",
                "validate": ["$200000", "$250000", "$300000", "$350000"],
                "expected_range": (200000, 400000)
            }
        ],
        "expected_total_value": 250000
    },
    
    "quality_optimization": {
        "name": "Quality-Cost Trade-off Analysis",
        "description": "Find the optimal balance between quality and cost",
        "steps": [
            {
                "prompt": "Analyze quality metrics and scrap rates across all products. What's the total annual cost of scrap?",
                "validate": ["scrap", "quality", "cost", "$"],
                "concepts": ["quality_metrics"]
            },
            {
                "prompt": "Which products have scrap rates above their targets? Focus on high-margin products.",
                "validate": ["Premium Juice", "scrap", "3%", "target"],
                "concepts": ["scrap_analysis"]
            },
            {
                "prompt": "For products with high scrap rates, what's the root cause? Is it related to equipment settings, raw materials, or process control?",
                "validate": ["process", "control", "inspection", "settings"],
                "concepts": ["root_cause_quality"]
            },
            {
                "prompt": "If we enhanced inspection and process control for high-margin products, what would be the ROI? Consider both cost and benefit.",
                "validate": ["ROI", "inspection", "$100000", "$150000", "$200000"],
                "expected_range": (100000, 250000)
            },
            {
                "prompt": "What's the payback period for implementing enhanced quality controls? Is it under 6 months?",
                "validate": ["payback", "3 month", "4 month", "5 month", "6 month"],
                "concepts": ["roi_calculation"]
            }
        ],
        "expected_total_value": 200000
    },
    
    "comprehensive_rollup": {
        "name": "Comprehensive Opportunity Summary",
        "description": "Roll up all discoveries into total opportunity",
        "steps": [
            {
                "prompt": "Summarize all the improvement opportunities we've discovered: LINE2-PCK issues, product-specific problems, temporal patterns, and quality improvements. What's the total annual opportunity?",
                "validate": ["LINE2-PCK", "Energy Drink", "Premium Juice", "pattern", "$"],
                "concepts": ["summary"]
            },
            {
                "prompt": "Create a prioritized action plan based on ROI and implementation complexity. Which improvements should we tackle first?",
                "validate": ["prioritize", "ROI", "LINE2-PCK", "first"],
                "concepts": ["prioritization"]
            },
            {
                "prompt": "What's the total financial opportunity if we implement all recommended improvements? Is it over $2M annually?",
                "validate": ["$2000000", "$2500000", "$3000000", "total"],
                "expected_range": (2000000, 3000000)
            }
        ],
        "expected_total_value": 2500000
    }
}

# Validation helpers for specific patterns
PATTERN_VALIDATORS = {
    "root_cause_analysis": [
        "jam", "material jam", "UNP-JAM", "sensor", "mechanical", 
        "calibration", "wear", "misalignment"
    ],
    "temporal_analysis": [
        "cluster", "pattern", "frequency", "time", "hour", 
        "minute", "periodic", "random"
    ],
    "shift_patterns": [
        "shift", "day shift", "night shift", "overnight", 
        "first shift", "second shift", "third shift"
    ],
    "product_specific_issues": [
        "foam", "viscosity", "temperature", "speed", "rate", 
        "reduction", "slower", "quality"
    ],
    "cascade_analysis": [
        "cascade", "downstream", "upstream", "bottleneck", 
        "propagate", "impact", "affect"
    ],
    "quality_metrics": [
        "scrap", "defect", "reject", "quality", "yield", 
        "first pass", "rework"
    ]
}

# Expected discoveries from manual prototype for validation
MANUAL_PROTOTYPE_TARGETS = {
    "line2_pck": {
        "value": 341000,  # Conservative estimate
        "findings": ["micro-stops", "jams", "81.5 hours", "342,650 units"]
    },
    "energy_drink": {
        "value": 710000,
        "findings": ["foaming", "15% speed reduction"]
    },
    "premium_juice": {
        "value": 97000,
        "findings": ["3% scrap", "quality issues"]
    },
    "temporal_patterns": {
        "value": 250000,
        "findings": ["60% cluster", "night shift 40% worse"]
    },
    "quality_overall": {
        "value": 200000,
        "findings": ["scrap reduction", "enhanced inspection"]
    }
}