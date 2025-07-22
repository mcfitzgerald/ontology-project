# Testing Guide for Discovery Agent

## Overview
The evaluation system is fully compatible with the refactored discovery agent. Multiple testing approaches are available.

## Prerequisites

1. **SPARQL API Running** ✓
   - Already confirmed running at http://localhost:8000
   - Health check shows ontology loaded with 34,800 events

2. **Google API Key**
   - Set environment variable: `export GOOGLE_API_KEY=your_key_here`
   - Required for actual LLM calls

## Testing Options

### 1. Structure Test (No API Key Required)
```bash
python test_agent_structure.py
```
Validates:
- Agent configuration
- Discovery methodology in instruction
- All 9 tools loaded
- State tracking enabled

### 2. ADK CLI Evaluation
```bash
# Discovery-first pattern test
adk eval manufacturing_agent evaluation/evalsets/discovery_first.evalset.json

# Hidden capacity analysis test
adk eval manufacturing_agent evaluation/evalsets/hidden_capacity.evalset.json

# With detailed results
adk eval manufacturing_agent evaluation/evalsets/discovery_first.evalset.json \
  --config_file_path=evaluation/test_config.json \
  --print_detailed_results
```

### 3. Pytest Suite
```bash
# Run all tests
pytest evaluation/test_agent_evaluation.py -v

# Run specific test
pytest evaluation/test_agent_evaluation.py::test_discovery_first -v

# With detailed output
pytest evaluation/test_agent_evaluation.py -v -s
```

### 4. Direct Python Testing
```python
# Run the discovery test
python test_discovery_agent.py

# Run evaluation programmatically
python evaluation/run_eval.py
```

## Available Test Suites

1. **discovery_first.evalset.json**
   - Tests that agent starts with entity discovery
   - Validates progression from simple to complex queries

2. **hidden_capacity.evalset.json**
   - Tests finding LINE2-PCK with 73.2% effective OEE
   - Validates $341K-$700K opportunity calculation

3. **microstop_pattern.evalset.json**
   - Tests temporal pattern recognition
   - Validates 60% clustering and shift variance findings

4. **quality_tradeoff.evalset.json**
   - Tests quality-cost analysis
   - Validates $200K scrap reduction opportunity

5. **manual_prototype_targets.evalset.json**
   - Tests against all key findings from manual prototype
   - Most comprehensive test suite

## Expected Results

The refactored agent should:
- ✓ Follow discovery-first pattern
- ✓ Use hypothesis tracking in SPARQL queries
- ✓ Apply discovery patterns (hidden_capacity, temporal_anomaly, etc.)
- ✓ Format insights with ROI and implementation steps
- ✓ Track discoveries in state throughout conversation

## Troubleshooting

1. **Import Errors**: Ensure you're in the adk_agents directory
2. **API Key Issues**: Set GOOGLE_API_KEY environment variable
3. **SPARQL Errors**: Check API is running at http://localhost:8000
4. **Tool Not Found**: Agent exports tools correctly, check imports

The evaluation system is fully operational and ready to validate the discovery agent's capabilities!