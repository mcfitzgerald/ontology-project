"""Python code execution tool for advanced data analysis."""
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
    - df: A pandas DataFrame with proper column names (if cache_id provided)
    - data: The raw query results as a list of lists (backward compatibility)
    - columns: List of column names from the SPARQL query
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
        # DataFrame 'df' is pre-loaded with proper column names
        print(f"Analyzing {len(df)} rows")
        print(f"Columns: {df.columns.tolist()}")
        
        # Your analysis here - access columns directly
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
            
            if cached_data and 'data' in cached_data:
                data = cached_data['data']
                
                # Handle API response format properly
                if 'columns' in data and 'results' in data:
                    # Create DataFrame with proper column names
                    columns = [col.replace('?', '') for col in data['columns']]
                    namespace['df'] = pd.DataFrame(data['results'], columns=columns)
                    
                    # Also provide raw data for backward compatibility
                    namespace['data'] = data['results']
                    namespace['columns'] = columns
                    
                    logger.info(f"Loaded DataFrame with {len(namespace['df'])} rows and columns: {columns}")
                elif 'results' in data:
                    # Fallback for old format or data without columns
                    namespace['data'] = data['results']
                    logger.warning("No column information found, using raw data")
                else:
                    # Direct data format
                    namespace['data'] = data
                    logger.warning("Using direct data format")
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
        if tool_context and hasattr(tool_context, 'state') and tool_context.state is not None:
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
        if tool_context and hasattr(tool_context, 'state') and tool_context.state is not None:
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