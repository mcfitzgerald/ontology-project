# ADK Manufacturing Agent Evaluation Framework

This evaluation framework tests the manufacturing analyst agents against proven patterns from the $2.5M optimization case study.

## Overview

The framework uses Google ADK's native evaluation capabilities enhanced with custom metrics specific to manufacturing analytics:

1. **Discovery-First Compliance** - Ensures agents start with entity discovery
2. **Proactive Execution** - Measures execution without unnecessary confirmations  
3. **Financial Accuracy** - Validates ROI calculations match expected ranges
4. **Pattern Recognition** - Confirms identification of key patterns (clustering, shifts)
5. **Actionable Insights** - Checks for specific, implementable recommendations

## Structure

```
evaluation/
├── evalsets/                          # Test cases in ADK format
│   ├── discovery_first.evalset.json   # Tests discovery-first pattern
│   ├── hidden_capacity.evalset.json   # Tests $341K-$700K opportunity finding
│   ├── microstop_pattern.evalset.json # Tests 60% clustering, 40% shift variance
│   └── quality_tradeoff.evalset.json  # Tests $200K quality improvement
├── test_config.json                   # Evaluation criteria and thresholds
├── test_agent_evaluation.py           # Main evaluation engine with custom metrics
├── generate_report.py                 # Human-readable report generator
└── reports/                           # Generated evaluation reports
```

## Running Evaluations

### Using ADK CLI

```bash
# Run a single test
adk eval manufacturing_agent evaluation/evalsets/discovery_first.evalset.json

# Run with configuration
adk eval manufacturing_agent evaluation/evalsets/hidden_capacity.evalset.json \
  --config_file_path=evaluation/test_config.json \
  --print_detailed_results
```

### Using Pytest

```bash
# Run all tests
pytest adk_agents/evaluation/test_agent_evaluation.py -v

# Run specific test suite
pytest adk_agents/evaluation/test_agent_evaluation.py::test_financial_analysis -v

# Generate detailed report
pytest adk_agents/evaluation/test_agent_evaluation.py::test_full_suite -v -s
```

### Direct Python Execution

```python
from evaluation.test_agent_evaluation import ManufacturingAgentEvaluator

evaluator = ManufacturingAgentEvaluator()
results = await evaluator.run_evaluation(
    agent_module="manufacturing_agent",
    test_suite="full_suite"
)
print(evaluator.generate_report())
```

## Test Cases

### 1. Discovery-First Pattern
Tests that agents follow the mandatory sequence:
- Entity discovery queries first
- Validation of entity names
- Building from simple to complex queries

### 2. Hidden Capacity Analysis  
Validates the agent can:
- Find LINE2-PCK with 73.2% effective OEE
- Calculate 11.8% capacity gain opportunity
- Quantify $341K-$700K annual value

### 3. Micro-Stop Pattern Recognition
Confirms agent identifies:
- 60% of jams occur within 10 minutes
- Night shift has 40% more issues
- Temporal clustering patterns

### 4. Quality-Cost Trade-off
Ensures agent can:
- Find 95.3% average quality (vs 98% target)
- Calculate $200K annual scrap reduction
- Recommend phased improvement approach

## Evaluation Metrics

### Core ADK Metrics
- **tool_trajectory_avg_score**: 85% - Tool usage matches expected sequence
- **response_match_score**: 75% - Response content aligns with expected

### Custom Manufacturing Metrics
- **discovery_first_compliance**: 90% - Starts with discovery queries
- **proactive_execution_rate**: 85% - Executes without confirmations
- **financial_calculation_accuracy**: 80% - ROI within expected range
- **pattern_recognition_quality**: 75% - Identifies key patterns
- **actionable_insights_score**: 85% - Provides specific actions

## Report Generation

### Summary Report
```bash
python evaluation/generate_report.py results.json summary
```

### Detailed Report
```bash
python evaluation/generate_report.py results.json detailed
```

### Comparison Report
```bash
python evaluation/generate_report.py run1.json run2.json run3.json comparison
```

## Expected Outcomes

Based on the manual prototype that discovered $2.5M in opportunities:

1. **Hidden Capacity**: $341K-$700K/year from equipment running below 75% effective OEE
2. **Pattern Recognition**: $250K-$350K/year from temporal clustering and shift patterns
3. **Quality Improvement**: $200K/year from reducing scrap below 98% quality target

Total expected value: $791K-$1.25M annually

### Flexible Validation

The evaluation framework now supports flexible validation that:
- Accepts multiple paths to the same insights
- Uses pattern matching rather than exact string comparison
- Provides partial credit for incremental discoveries
- Focuses on outcomes rather than specific methods

See `INSIGHTS_GUIDE.md` for types of insights to discover.

## Integration with CI/CD

Add to your CI pipeline:

```yaml
test-agent:
  script:
    - pytest adk_agents/evaluation/test_agent_evaluation.py
  artifacts:
    paths:
      - adk_agents/evaluation/reports/
```

## Extending the Framework

To add new test cases:

1. Create a new `.evalset.json` file in `evalsets/`
2. Add expected outcomes to `test_config.json`
3. Implement custom metrics in `test_agent_evaluation.py` if needed
4. Update test suites in configuration

The framework is designed to be extensible while maintaining compatibility with ADK's native evaluation system.