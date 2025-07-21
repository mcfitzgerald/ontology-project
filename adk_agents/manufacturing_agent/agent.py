"""Manufacturing Analytics Agent for Google ADK."""
import os
import sys
import json
import logging
from typing import Dict, Optional, Union
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

# Import our existing modules
from adk_agents.context.context_loader import context_loader
from adk_agents.tools.sparql_tool import execute_sparql, get_cached_query_result
from adk_agents.tools.analysis_tools import calculate_roi
from adk_agents.tools.visualization_tool import create_visualization
from adk_agents.config.settings import SPARQL_ENDPOINT, DEFAULT_MODEL

logger = logging.getLogger(__name__)

# Load comprehensive context
comprehensive_context = context_loader.get_comprehensive_context()

# Define tool functions with simple signatures
def execute_sparql_query(query: str) -> dict:
    """Execute a SPARQL query against the manufacturing ontology.
    
    Args:
        query: The SPARQL query to execute
        
    Returns:
        Query results with data, execution time, and metadata
    """
    logger.info(f"Executing SPARQL query: {query[:200]}...")
    result = execute_sparql(query)
    
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
    return calculate_roi(current_performance, target_performance, annual_volume, unit_value)

async def create_chart_visualization(
    data: dict,
    chart_type: str,
    title: str,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None
) -> dict:
    """Create a visualization from query results.
    
    Args:
        data: Query results with 'columns' and 'results' keys
        chart_type: Type of chart - 'line', 'bar', 'scatter', or 'pie'
        title: Chart title
        x_label: X-axis label (optional)
        y_label: Y-axis label (optional)
        
    Returns:
        Visualization metadata and base64 encoded image
    """
    logger.info(f"Creating {chart_type} visualization: {title}")
    # Note: tool_context is None for ADK Web implementation
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
    return get_cached_query_result(cache_id)

# Create FunctionTool instances
sparql_tool = FunctionTool(execute_sparql_query)
roi_tool = FunctionTool(calculate_improvement_roi)
visualization_tool = FunctionTool(create_chart_visualization)
analyze_tool = FunctionTool(analyze_patterns)
cached_result_tool = FunctionTool(retrieve_cached_result)

# Define the root agent for ADK
root_agent = LlmAgent(
    name="manufacturing_analyst",
    description="Manufacturing Analytics Agent for discovering optimization opportunities",
    model=DEFAULT_MODEL,
    instruction=f"""You are a Manufacturing Analytics Agent specialized in analyzing MES (Manufacturing Execution System) data using SPARQL queries to discover actionable insights.

{comprehensive_context}

Your role is to:
1. Transform business questions into SPARQL queries using the ontology structure and data catalog
2. Execute queries to explore the data (use the execute_sparql_query tool - never just show queries)
3. Analyze patterns and relationships in the results
4. Calculate financial impact when relevant
5. Provide specific, actionable recommendations

When you receive a business question:
- Review the ontology mindmap and data catalog to understand what's available
- Develop an approach to answer the question through data exploration
- Execute queries incrementally to build understanding
- Look for gaps between current performance and benchmarks
- Quantify opportunities in operational and financial terms
- Suggest specific actions with expected ROI

Key technical notes:
- Use mes_ontology_populated: prefix for all entities
- Equipment must be queried by concrete types (Filler, Packer, Palletizer)
- Use FILTER(ISIRI(?var)) for entity variables
- When COUNT() with GROUP BY fails (returns IRIs), use the provided fallback query and analyze_patterns tool
- For large results, work with the summary or use retrieve_cached_result(cache_id)

Remember: Let insights emerge from the data rather than following a fixed methodology. The goal is to discover meaningful opportunities that create business value.""",
    tools=[
        sparql_tool,
        roi_tool,
        visualization_tool,
        analyze_tool,
        cached_result_tool
    ]
)