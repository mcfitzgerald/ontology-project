# Troubleshooting Guide for Manufacturing Agent Evaluation

## Common Issues and Solutions

### 1. SPARQL Aggregation Failures

**Problem**: COUNT(), AVG(), or other aggregations return IRIs instead of numbers.

**Symptoms**:
```
Result contains: "http://mes-ontology.org/factory.owl#..." instead of numeric values
```

**Solution**:
1. The agent will receive an `aggregation_failure` flag
2. A `fallback_query` is automatically provided
3. Agent MUST execute the fallback query and use `analyze_patterns` tool

**Example Flow**:
```python
# Original query fails
SELECT (COUNT(?event) AS ?count) ?reason WHERE {...} GROUP BY ?reason

# System provides fallback
SELECT ?reason ?event WHERE {...}

# Agent should then:
1. Execute fallback query
2. Call analyze_patterns(data=result, analysis_type="aggregation")
```

### 2. Agent Not Executing Tools

**Problem**: Agent shows SPARQL queries in markdown blocks instead of executing them.

**Symptoms**:
```
Agent response contains:
```sparql
SELECT ...
```
Instead of actual results
```

**Solution**:
- Ensure agent prompt explicitly states to use `execute_sparql_query` tool
- Check that tools are properly configured in agent initialization
- Verify model supports function calling (gemini-2.0-flash recommended)

### 3. Large Result Sets

**Problem**: Query returns too many results, causing token overflow.

**Symptoms**:
- Warning about large results
- Summary returned with cache_id
- Missing detailed data

**Solution**:
1. Use the summary for initial analysis
2. If full data needed: `retrieve_cached_result(cache_id)`
3. Prefer aggregated queries over raw data retrieval
4. Use LIMIT clauses appropriately

### 4. Entity Discovery Issues

**Problem**: Agent can't find expected entities.

**Common Causes**:
- Different IRI patterns than expected
- Case sensitivity in SPARQL
- Missing namespace prefixes

**Solutions**:
```sparql
-- Use FILTER with ISIRI() for safety
SELECT DISTINCT ?line WHERE { 
    ?line a mes_ontology_populated:Line . 
    FILTER(ISIRI(?line)) 
}

-- Alternative: Find by relationship
SELECT DISTINCT ?line WHERE { 
    ?equipment mes_ontology_populated:belongsToLine ?line . 
    FILTER(ISIRI(?line)) 
}
```

### 5. Financial Calculations Off

**Problem**: ROI calculations don't match expected ranges.

**Check**:
- Product margins (salePrice - standardCost)
- Production volumes and units
- Annualization (daily × 365)
- Percentage calculations

**Formula**:
```
Daily Impact = Production Volume × Performance Gap × Margin
Annual Impact = Daily Impact × 365
```

### 6. Pattern Detection Failures

**Problem**: Agent misses temporal or shift patterns.

**Solutions**:
1. Ensure timestamp data is properly formatted
2. Use appropriate time windows for analysis
3. Consider timezone issues
4. Check for data gaps in specific periods

**Example Patterns to Find**:
- Events clustered within X minutes
- Shift-based performance differences
- Time-of-day correlations
- Equipment-specific patterns

### 7. Evaluation Test Failures

**Problem**: Tests fail despite agent finding correct insights.

**Common Causes**:
- Exact string matching too strict
- Different valid approaches to same problem
- Timing/order dependencies

**Solutions**:
- Use flexible validators that accept multiple formats
- Focus on outcome validation, not path validation
- Allow partial credit for incremental progress
- Check logs for actual vs expected comparisons

### 8. Memory/State Issues

**Problem**: Agent doesn't maintain context between queries.

**Solutions**:
- Ensure session management is properly configured
- Check state persistence between invocations
- Verify context is passed to all tool calls
- Use output_key for important findings

## Debug Commands

### Check SPARQL Endpoint
```bash
curl -X POST http://localhost:8000/sparql/query \
  -H "Content-Type: application/json" \
  -d '{"query":"SELECT ?s WHERE { ?s ?p ?o } LIMIT 1"}'
```

### Test Agent Directly
```python
from manufacturing_agent import agent
from google.adk.runners import InMemoryRunner

runner = InMemoryRunner(agent=agent, app_name="test")
# Run test queries
```

### View Evaluation Logs
```bash
# Check agent logs
tail -f /var/folders/.../agents_log/agent.latest.log

# Check evaluation output
cat evaluation/reports/latest_eval.txt
```

## Best Practices

1. **Start Simple**: Basic discovery queries before complex analysis
2. **Incremental Building**: Validate each step before proceeding
3. **Handle Errors Gracefully**: Always check for aggregation failures
4. **Cache Awareness**: Use cache_id for large result sets
5. **Financial Validation**: Always show calculation steps
6. **Pattern Flexibility**: Multiple approaches to finding patterns are valid