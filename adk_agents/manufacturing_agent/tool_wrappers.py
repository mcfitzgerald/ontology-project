"""Tool wrappers for ADK compatibility - removes optional parameters"""
import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

def execute_sparql_query(query: str) -> dict:
    """Execute a SPARQL query against the manufacturing ontology.
    
    Args:
        query: The SPARQL query to execute
        
    Returns:
        Query results with data, execution time, metadata, and next questions
    """
    logger.info(f"Executing SPARQL query: {query[:200]}...")
    
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
            "2. Use analyze_patterns(data=<result>, analysis_type='aggregation')\n"
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

def calculate_improvement_roi(
    current_performance: float,
    target_performance: float,
    annual_volume: float,
    unit_value: float
) -> dict:
    """Calculate ROI for performance improvements.
    
    Args:
        current_performance: Current OEE or performance percentage
        target_performance: Target OEE or performance percentage
        annual_volume: Annual production volume in units
        unit_value: Value per unit in dollars
        
    Returns:
        ROI analysis with financial projections
    """
    logger.info(f"Calculating ROI: {current_performance}% -> {target_performance}%")
    from adk_agents.tools.analysis_tools import calculate_roi
    return calculate_roi(current_performance, target_performance, annual_volume, unit_value)

async def create_chart_visualization(
    data: dict,
    chart_type: str,
    title: str,
    x_label: str,
    y_label: str
) -> dict:
    """Create a visualization from query results.
    
    Args:
        data: Query results with 'columns' and 'results' keys
        chart_type: Type of chart - 'line', 'bar', 'scatter', or 'pie'
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        
    Returns:
        Visualization metadata and base64 encoded image
    """
    logger.info(f"Creating {chart_type} visualization: {title}")
    from adk_agents.tools.visualization_tool import create_visualization
    # Await the async function directly
    return await create_visualization(data, chart_type, title, x_label, y_label, None)

def analyze_patterns(data: dict, analysis_type: str) -> dict:
    """Analyze patterns in query results.
    
    Args:
        data: Query results from SPARQL
        analysis_type: Type of analysis - temporal, capacity, quality, aggregation, or general
        
    Returns:
        Analysis results with insights
    """
    logger.info(f"Analyzing patterns: {analysis_type}")
    
    # Handle case where data might be passed as a string description
    if isinstance(data, str):
        return {"error": f"Expected query results but received description: {data}"}
    
    # Ensure data is a dict or list
    if not isinstance(data, (dict, list)):
        return {"error": f"Expected dict or list but received {type(data).__name__}"}
        
    from adk_agents.tools.analysis_tools import analyze_patterns as analyze_patterns_impl
    return analyze_patterns_impl(data, analysis_type)

def retrieve_cached_result(cache_id: str) -> dict:
    """Retrieve full cached query result by ID.
    
    Args:
        cache_id: The cache ID returned from a previous query
        
    Returns:
        Full query result or error if not found
    """
    logger.info(f"Retrieving cached result: {cache_id}")
    from adk_agents.tools.sparql_tool import get_cached_query_result
    return get_cached_query_result(cache_id)

def get_discovery_pattern(pattern_name: str, context: str) -> dict:
    """Get a discovery pattern with filled context.
    
    Args:
        pattern_name: Name of the pattern
        context: Context to fill the pattern with
        
    Returns:
        Pattern with queries and next steps
    """
    from adk_agents.tools.discovery_patterns import get_discovery_pattern as get_pattern_impl
    return get_pattern_impl(pattern_name, context, None)

def list_discovery_patterns() -> Dict[str, Any]:
    """List all available discovery patterns.
    
    Returns:
        Dictionary of patterns and their descriptions
    """
    from adk_agents.tools.discovery_patterns import list_discovery_patterns as list_patterns_impl
    return list_patterns_impl(None)

def format_insight(
    finding: str,
    evidence: dict,
    impact: float,
    action: str,
    confidence: float
) -> dict:
    """Format a discovery into an executive-ready insight.
    
    Args:
        finding: The key discovery or insight
        evidence: Data supporting the finding (queries, metrics, patterns)
        impact: Annual financial impact in dollars
        action: Recommended action to capture the opportunity
        confidence: Confidence level (0-1) in the finding
        
    Returns:
        Formatted insight with all details
    """
    from adk_agents.tools.insight_formatter import format_insight as format_impl
    return format_impl(finding, evidence, impact, action, confidence, None)

def create_executive_summary(insights: str) -> dict:
    """Create an executive summary from multiple insights.
    
    Args:
        insights: JSON string of formatted insights list
        
    Returns:
        Executive summary with total impact and prioritized actions
    """
    from adk_agents.tools.insight_formatter import create_executive_summary as summary_impl
    import json
    # Parse JSON string to list
    insights_list = json.loads(insights) if isinstance(insights, str) else insights
    return summary_impl(insights_list, None)

def execute_python_code(code: str, cache_id: str) -> dict:
    """Execute Python code for data analysis with cached query results.
    
    Args:
        code: Python code to execute
        cache_id: Cache ID of the query result to analyze
        
    Returns:
        Execution results including output, visualizations, and any errors
    """
    from adk_agents.tools.python_executor import execute_python_code as execute_impl
    return execute_impl(code, cache_id, None)