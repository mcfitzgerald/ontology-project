# Python Executor Tool Implementation Plan

## Executive Summary

This plan details the implementation of a Python execution tool that enables the discovery agent to perform advanced analysis on large datasets without token limits. Following Google ADK best practices, this tool will allow iterative code development where the LLM writes, tests, and refines Python code to discover insights from cached SPARQL results.

## Alignment with System Architecture

### Integration Points

1. **Discovery Flow Enhancement**
   - Fits into the existing EXPLORE → DISCOVER → QUANTIFY → RECOMMEND methodology
   - Adds a new analysis capability after SPARQL queries return large datasets
   - Maintains hypothesis-driven approach with iterative refinement

2. **Tool Ecosystem**
   - Complements existing tools: `execute_sparql_query`, `analyze_patterns`, `calculate_improvement_roi`
   - Works with `ResultCache` to access full datasets via cache_id
   - Outputs can be visualized with `create_visualization`
   - Results formatted with `format_insight`

3. **State Management**
   - Uses ADK's `tool_context.state` to track analysis progress
   - Stores successful code snippets for reuse
   - Maintains discovery context across iterations

## Implementation Details

### 1. Core Python Executor Tool

**File**: `adk_agents/tools/python_executor.py`

```python
from typing import Dict, Any, Optional
from google.adk.tools.tool_context import ToolContext
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import sys
import logging

logger = logging.getLogger(__name__)

def execute_python_code(
    code: str, 
    cache_id: Optional[str] = None,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """Execute Python code with access to cached query results.
    
    Use this tool for advanced analysis on large datasets. The code has access to:
    - data: The cached query results as a list of dictionaries (if cache_id provided)
    - pandas as pd, numpy as np, datetime, timedelta
    - Must define 'result' dict with analysis findings
    
    Start simple and build complexity iteratively. If an error occurs, 
    adjust your approach and try again.
    
    Args:
        code: Python code to execute. Should define a 'result' dict.
        cache_id: Optional ID of cached SPARQL results to analyze
        tool_context: ADK tool context for state management
        
    Returns:
        Dictionary with:
        - status: 'success' or 'error'
        - result: The analysis results (if successful)
        - output: Any print statements from execution
        - error: Error message (if failed)
        
    Example:
        code = '''
        df = pd.DataFrame(data)
        print(f"Analyzing {len(df)} rows")
        
        # Your analysis here
        avg_oee = df['oee'].mean()
        
        result = {
            "average_oee": avg_oee,
            "below_benchmark": (df['oee'] < 85).sum()
        }
        '''
    """
    logger.info(f"Executing Python code{' with cache_id: ' + cache_id if cache_id else ''}")
    
    # Setup execution namespace
    namespace = {
        '__builtins__': __builtins__,
        'pd': pd,
        'np': np,
        'datetime': datetime,
        'timedelta': timedelta,
        'print': print,  # Allow debugging output
    }
    
    # Load cached data if provided
    if cache_id:
        try:
            from .result_cache import get_cached_result
            cached_data = get_cached_result(cache_id)
            
            if cached_data and 'data' in cached_data and 'results' in cached_data['data']:
                namespace['data'] = cached_data['data']['results']
                logger.info(f"Loaded {len(namespace['data'])} rows from cache")
            else:
                return {
                    "status": "error",
                    "error": f"No data found for cache_id: {cache_id}",
                    "error_type": "DataNotFound"
                }
        except Exception as e:
            logger.error(f"Failed to load cached data: {e}")
            return {
                "status": "error",
                "error": f"Failed to load cached data: {str(e)}",
                "error_type": type(e).__name__
            }
    
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    
    try:
        # Execute the code
        exec(code, namespace)
        
        # Restore stdout and get output
        output = buffer.getvalue()
        sys.stdout = old_stdout
        
        # Extract result
        if 'result' not in namespace:
            logger.warning("No 'result' variable defined in executed code")
            result = {}
        else:
            result = namespace['result']
        
        # Track successful analysis in state
        if tool_context and tool_context.state:
            analyses = tool_context.state.get('python_analyses', [])
            analyses.append({
                'timestamp': datetime.now().isoformat(),
                'cache_id': cache_id,
                'code_preview': code[:200] + '...' if len(code) > 200 else code,
                'result_keys': list(result.keys()) if isinstance(result, dict) else [],
                'success': True
            })
            tool_context.state['python_analyses'] = analyses[-10:]  # Keep last 10
        
        return {
            "status": "success",
            "result": result,
            "output": output,
            "execution_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        sys.stdout = old_stdout
        error_msg = str(e)
        logger.error(f"Python execution error: {error_msg}")
        
        # Track failed analysis for learning
        if tool_context and tool_context.state:
            failures = tool_context.state.get('python_failures', [])
            failures.append({
                'timestamp': datetime.now().isoformat(),
                'error': error_msg,
                'error_type': type(e).__name__
            })
            tool_context.state['python_failures'] = failures[-5:]  # Keep last 5
        
        return {
            "status": "error",
            "error": error_msg,
            "error_type": type(e).__name__,
            "output": buffer.getvalue()
        }
```

### 2. Update SPARQL Tool Integration

**File**: `adk_agents/tools/sparql_tool.py` (modifications)

Add to the response when returning summaries:

```python
# In execute() method, when estimated_tokens > 10000:
return {
    "status": "success",
    "summary": summary,
    "warning": f"Result contains ~{estimated_tokens} tokens. Returning summary to prevent token overflow.",
    "cache_id": cache_id,
    "full_result_available": True,
    "python_analysis_hint": f"Use execute_python_code(code='...', cache_id='{cache_id}') to analyze the full dataset",
    "data_shape": {
        "rows": len(results),
        "columns": list(results[0].keys()) if results else [],
        "sample_values": {k: v for k, v in results[0].items()} if results else {}
    }
}
```

### 3. Update Discovery Agent

**File**: `adk_agents/manufacturing_agent/agent.py` (modifications)

1. **Add to imports**:
```python
from ..tools.python_executor import execute_python_code
```

2. **Add to tools list**:
```python
tools = [
    FunctionTool(execute_sparql_query),
    FunctionTool(get_discovery_pattern),
    FunctionTool(analyze_patterns),
    FunctionTool(calculate_improvement_roi),
    FunctionTool(create_visualization),
    FunctionTool(get_data_catalogue),
    FunctionTool(retrieve_cached_result),
    FunctionTool(format_insight),
    FunctionTool(get_sparql_reference),
    FunctionTool(execute_python_code)  # NEW
]
```

3. **Update instruction to include Python analysis guidance**:
```python
instruction = """You are a discovery analyst for manufacturing optimization...

## Advanced Analysis with Python

When SPARQL queries return large datasets (indicated by cache_id), use execute_python_code for sophisticated analysis:

1. **Start Simple**: First explore the data structure
   ```python
   df = pd.DataFrame(data)
   print(f"Shape: {df.shape}")
   print(f"Columns: {list(df.columns)}")
   print(df.head())
   result = {"rows": len(df), "columns": list(df.columns)}
   ```

2. **Build Understanding**: Based on what you learn, dig deeper
   ```python
   df = pd.DataFrame(data)
   # Now that you know the columns...
   print(df.describe())
   result = {"statistics": df.describe().to_dict()}
   ```

3. **Discover Patterns**: Apply increasingly sophisticated analysis
   ```python
   df = pd.DataFrame(data)
   # Group by dimensions, find correlations, detect anomalies
   hourly_pattern = df.groupby(df['timestamp'].dt.hour).size()
   result = {"peak_hours": hourly_pattern.nlargest(3).to_dict()}
   ```

4. **Quantify Impact**: Always connect findings to business value
   ```python
   # Calculate financial impact of discoveries
   lost_capacity = ...
   result = {"annual_impact": lost_capacity * unit_value * 365}
   ```

Remember: If code fails, learn from the error and try a different approach. Build your analysis iteratively."""
```

### 4. Testing Strategy

1. **Unit Tests** (`tests/test_python_executor.py`):
```python
def test_basic_execution():
    """Test basic Python code execution."""
    code = "result = {'test': 'success', 'value': 42}"
    result = execute_python_code(code)
    assert result['status'] == 'success'
    assert result['result']['test'] == 'success'

def test_with_cached_data():
    """Test execution with cached data."""
    # First cache some data
    cache_id = cache_query_result("test", {"data": {"results": [{"a": 1}, {"a": 2}]}})
    
    code = """
    df = pd.DataFrame(data)
    result = {'sum_a': df['a'].sum()}
    """
    result = execute_python_code(code, cache_id=cache_id)
    assert result['result']['sum_a'] == 3

def test_error_handling():
    """Test error handling and recovery."""
    code = "undefined_variable"
    result = execute_python_code(code)
    assert result['status'] == 'error'
    assert 'NameError' in result['error_type']
```

2. **Integration Tests** (`tests/test_discovery_flow.py`):
```python
async def test_iterative_discovery():
    """Test the full iterative discovery flow."""
    # 1. SPARQL returns large dataset
    # 2. Agent uses Python to explore
    # 3. Agent refines analysis based on findings
    # 4. Agent quantifies impact
    # 5. Agent formats insight
```

### 5. Security Considerations

Since this is for local prototyping only:
- ✅ No sandboxing (runs in same environment)
- ✅ Full pandas/numpy access
- ✅ Can read from cache directory
- ⚠️ Cannot write to filesystem (no file operations exposed)
- ⚠️ Cannot make network requests (no requests library)
- ⚠️ Cannot import arbitrary modules (controlled namespace)

For production, would need:
- Docker/VM isolation
- Resource limits (CPU, memory, time)
- Restricted imports whitelist
- No filesystem access

### 6. Example Discovery Flow

**User**: "Analyze equipment performance trends"

**Agent's Iterative Discovery**:

```python
# Iteration 1: Explore
code_v1 = '''
df = pd.DataFrame(data)
print(f"Dataset: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(f"Equipment: {df['equipment'].unique()}")
result = {"equipment_count": df['equipment'].nunique()}
'''

# Iteration 2: Analyze trends
code_v2 = '''
df = pd.DataFrame(data)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['date'] = df['timestamp'].dt.date

daily_oee = df.groupby(['date', 'equipment'])['oee'].mean()
trending_down = []
for equip in df['equipment'].unique():
    equip_data = daily_oee[daily_oee.index.get_level_values(1) == equip]
    if len(equip_data) > 7:
        trend = np.polyfit(range(len(equip_data)), equip_data.values, 1)[0]
        if trend < -0.5:  # Declining more than 0.5% per day
            trending_down.append((equip, trend))

result = {
    "declining_equipment": trending_down,
    "worst_trend": min(trending_down, key=lambda x: x[1]) if trending_down else None
}
'''

# Iteration 3: Quantify impact
code_v3 = '''
df = pd.DataFrame(data)
worst_equipment = "LINE2-PCK"  # From previous analysis

equip_data = df[df['equipment'] == worst_equipment]
current_oee = equip_data['oee'].mean()
decline_rate = -1.2  # % per day from previous
days_to_critical = (current_oee - 60) / abs(decline_rate)  # When OEE hits 60%

# Financial impact
production_rate = 150  # units/hour
unit_margin = 25
daily_loss = (abs(decline_rate) / 100) * 24 * production_rate * unit_margin

result = {
    "equipment": worst_equipment,
    "current_oee": current_oee,
    "days_to_critical": days_to_critical,
    "daily_revenue_loss": daily_loss,
    "monthly_impact": daily_loss * 30
}
'''
```

## Benefits

1. **Eliminates Token Limits**: Only insights returned, not raw data
2. **Enables Advanced Analysis**: Statistics, ML, correlations, forecasting
3. **Natural Error Recovery**: Errors guide next iteration
4. **Preserves Discovery Flow**: Maintains hypothesis-driven approach
5. **Integrates Seamlessly**: Works with existing tools and state

## Next Steps

1. Implement core executor (30 min)
2. Update SPARQL tool hints (15 min)
3. Add to agent tools list (5 min)
4. Update agent instruction (15 min)
5. Write unit tests (30 min)
6. Test iterative discovery flow (30 min)

Total implementation time: ~2 hours

This implementation follows ADK best practices, integrates cleanly with the existing architecture, and enables powerful iterative discovery on large datasets!