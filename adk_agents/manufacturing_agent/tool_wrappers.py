"""Tool wrappers for ADK compatibility - removes optional parameters"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

def execute_sparql_query(query: str, tool_context: Optional[ToolContext] = None) -> dict:
    """Execute a SPARQL query against the manufacturing ontology.
    
    Args:
        query: The SPARQL query to execute
        tool_context: Optional ADK tool context for state management
        
    Returns:
        Query results with data, execution time, metadata, and next questions
    """
    logger.info(f"Executing SPARQL query: {query[:200]}...")
    
    # Update analysis phase if tool context is available
    if tool_context and hasattr(tool_context, 'state') and tool_context.state is not None:
        tool_context.state['analysis_phase'] = 'sparql_construction'
        logger.debug("Updated analysis phase to 'sparql_construction'")
    
    from adk_agents.tools.sparql_tool import execute_sparql
    result = execute_sparql(query)
    
    # Add next questions based on results
    result["next_questions"] = suggest_next_questions(result)
    
    # Check if aggregation failure was detected
    if result.get("aggregation_failure", False):
        logger.warning("SPARQL aggregation failure detected - suggesting Python fallback")
        
        # Add a more prominent warning for the LLM
        result["action_required"] = (
            "CRITICAL: This aggregation query failed because SPARQL returned IRIs instead of numbers.\n"
            "You MUST follow these steps:\n"
            "1. Execute the provided fallback_query immediately\n"
            "2. Use execute_python_code to perform aggregation/counting with pandas\n"
            "3. The Python tool will perform the counting/averaging correctly\n"
            "DO NOT proceed without using the fallback approach!"
        )
    
    return result

def suggest_next_questions(result: dict) -> List[str]:
    """Suggest follow-up questions based on query results."""
    suggestions = []
    
    if "data" in result and result["data"].get("results"):
        row_count = len(result["data"]["results"])
        
        # Based on result characteristics
        if row_count == 0:
            suggestions.append("No data found - try broadening the query or checking different time periods")
        elif row_count == 1:
            suggestions.append("Single result - investigate why this is unique")
        elif row_count > 100:
            suggestions.append("Large dataset - consider aggregating by time or category")
    
    return suggestions

# ROI calculation removed - use execute_python_code for flexible analysis

# Visualization removed - use execute_python_code with matplotlib for flexible charting

# Pattern analysis removed - use execute_python_code for flexible data analysis

def retrieve_cached_result(cache_id: str, tool_context: Optional[ToolContext] = None) -> dict:
    """Retrieve full cached query result by ID.
    
    Args:
        cache_id: The cache ID returned from a previous query
        tool_context: Optional ADK tool context for state management
        
    Returns:
        Full query result or error if not found
    """
    logger.info(f"Retrieving cached result: {cache_id}")
    from adk_agents.tools.sparql_tool import get_cached_query_result
    return get_cached_query_result(cache_id)

# Discovery patterns removed - let LLM discover patterns naturally

# Insight formatting removed - let LLM format insights contextually

def execute_python_code(code: str, cache_id: str, tool_context: Optional[ToolContext] = None) -> dict:
    """Execute Python code for data analysis with cached query results.
    
    Args:
        code: Python code to execute
        cache_id: Cache ID of the query result to analyze
        tool_context: Optional ADK tool context for state management
        
    Returns:
        Execution results including output, visualizations, and any errors
    """
    # Update analysis phase if tool context is available
    if tool_context and hasattr(tool_context, 'state') and tool_context.state is not None:
        tool_context.state['analysis_phase'] = 'python_analysis'
        logger.debug("Updated analysis phase to 'python_analysis'")
    
    from adk_agents.tools.python_executor import execute_python_code as execute_impl
    return execute_impl(code, cache_id, tool_context)