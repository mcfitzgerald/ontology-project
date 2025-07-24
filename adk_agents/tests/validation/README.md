# ADK Agent Validation Framework

This validation framework tests the ADK manufacturing agent against the manual prototype benchmarks that discovered $2.5M+ in optimization opportunities.

## Overview

The validation framework is **completely separate** from the agent system and only tests it from the outside using ADK's standard Runner and session management tools. It focuses on **outcome-based validation** rather than trajectory matching.

## Key Components

### 1. `manual_prototype_validator.py`
Core validation class that:
- Runs the agent through business scenarios
- Extracts financial discoveries and entities
- Compares outcomes to manual prototype benchmarks
- Generates detailed validation reports

### 2. `scenario_definitions.py`
Defines test scenarios based on manual prototype:
- Hidden Capacity: LINE2-PCK micro-stops ($341K-$700K)
- Product OEE: Energy Drink foaming, Premium Juice scrap ($806K)
- Temporal Patterns: Micro-stop clustering ($250K-$350K)
- Quality Trade-offs: Scrap reduction opportunities ($200K)

### 3. `outcome_evaluator.py`
Sophisticated extraction and evaluation:
- Financial value extraction with deduplication
- Entity recognition (equipment, products, patterns)
- Insight classification and scoring
- Achievement score calculation

### 4. `run_validation.py`
Main test runner that:
- Executes all validation scenarios
- Generates comprehensive reports
- Compares results to $2.5M benchmark
- Saves detailed JSON and summary reports

## Running Validation

### Quick Start
```bash
# Run full validation
python adk_agents/tests/validation/run_validation.py

# Run with verbose output
python adk_agents/tests/validation/run_validation.py --verbose

# Run without saving report
python adk_agents/tests/validation/run_validation.py --no-save
```

### Using pytest
```bash
# Run all integration tests
pytest adk_agents/tests/integration/test_manual_prototype_scenarios.py -v

# Run specific test
pytest adk_agents/tests/integration/test_manual_prototype_scenarios.py::TestManualPrototypeScenarios::test_hidden_capacity_discovery -v
```

## Success Criteria

The agent is considered successful if it:
1. **Financial Discovery**: Finds ≥80% of manual prototype value ($2M+ of $2.5M)
2. **Entity Recognition**: Identifies key equipment (LINE2-PCK) and products
3. **Pattern Detection**: Discovers at least 3 of 5 pattern types
4. **Actionable Insights**: Provides specific recommendations with ROI

## Validation Metrics

- **Achievement Rate**: Total value found / $2.5M target
- **Entity Coverage**: Key equipment and products identified
- **Pattern Recognition**: Temporal and quality patterns discovered
- **Recommendation Quality**: Actionable insights with financial quantification

## Example Output

```
VALIDATION SUMMARY
================================================================================

Overall Status: ✅ PASSED
Achievement Rate: 92.4%
Total Value Found: $2,310,000
Scenarios Run: 5
Avg Response Time: 3.45s

Validation Results:
  ✅ total_value:
     Found: $2,310,000 (target: $2,500,000)
     Achievement: 92.4%
  ✅ hidden_capacity:
     LINE2-PCK found: True
     Root cause identified: True
  ✅ product_oee:
     Energy Drink issue: True
     Premium Juice issue: True
  ✅ patterns:
     Patterns found: 7
     Key patterns: cascade, cluster, night shift

Key Discoveries:
  Equipment: LINE2-PCK, LINE3-FIL, LINE1
  Products: Energy Drink, Premium Juice, Soda
  Total patterns: 12
```

## Important Notes

1. **Isolation**: This framework is completely isolated from the agent system
2. **Flexibility**: Allows different discovery paths to same insights
3. **Business Focus**: Measures actual value, not technical execution
4. **No Modifications**: Never modifies agent code, only tests from outside

## Troubleshooting

If validation fails:
1. Check that SPARQL API is running on port 8000
2. Ensure agent module path is correct
3. Review detailed JSON report for specific failures
4. Check agent logs for query execution issues