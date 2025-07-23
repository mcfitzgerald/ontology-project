"""Manufacturing Analytics Agent for Google ADK."""
import os
import sys
import json
import logging
from typing import Dict, Optional, Union, List
from pathlib import Path
from datetime import datetime

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

# Import our existing modules
from adk_agents.context.context_loader import context_loader
from adk_agents.tools.sparql_tool import execute_sparql, get_cached_query_result
from adk_agents.tools.analysis_tools import calculate_roi
from adk_agents.tools.visualization_tool import create_visualization
from adk_agents.tools.discovery_patterns import get_discovery_pattern, list_discovery_patterns
from adk_agents.tools.insight_formatter import format_insight, create_executive_summary
from adk_agents.tools.python_executor import execute_python_code
from adk_agents.config.settings import SPARQL_ENDPOINT, DEFAULT_MODEL

logger = logging.getLogger(__name__)

# Load comprehensive context
comprehensive_context = context_loader.get_comprehensive_context()

# Import ToolContext for state management
from google.adk.tools.tool_context import ToolContext

# Define tool functions with simple signatures
def execute_sparql_query(query: str, hypothesis: Optional[str] = None, tool_context: Optional[ToolContext] = None) -> dict:
    """Execute a SPARQL query against the manufacturing ontology with discovery tracking.
    
    Args:
        query: The SPARQL query to execute
        hypothesis: What you're trying to discover with this query
        tool_context: ADK tool context for state management
        
    Returns:
        Query results with data, execution time, metadata, and next questions
    """
    logger.info(f"Executing SPARQL query: {query[:200]}...")
    if hypothesis:
        logger.info(f"Testing hypothesis: {hypothesis}")
    
    result = execute_sparql(query)
    
    # Track discoveries in state
    if tool_context and hypothesis and "data" in result and result["data"].get("results"):
        discoveries = tool_context.state.get("discoveries", [])
        
        # Analyze result for patterns
        data_rows = result["data"]["results"]
        pattern_insights = []
        
        # Look for anomalies or interesting patterns
        if len(data_rows) > 0:
            # Example pattern detection
            if "oee" in str(data_rows[0]).lower() or "performance" in str(data_rows[0]).lower():
                # Check for below-benchmark performance
                for row in data_rows[:10]:  # Sample first 10
                    if isinstance(row, list):
                        for val in row:
                            try:
                                if isinstance(val, (int, float)) and 0 < val < 85:
                                    pattern_insights.append(f"Found sub-benchmark performance: {val}%")
                                    break
                            except:
                                pass
            
            # Track the discovery
            discoveries.append({
                "hypothesis": hypothesis,
                "query": query[:200] + "..." if len(query) > 200 else query,
                "row_count": len(data_rows),
                "patterns": pattern_insights,
                "timestamp": datetime.now().isoformat()
            })
            tool_context.state["discoveries"] = discoveries
            
            # Track value found
            total_value = tool_context.state.get("total_value_found", 0)
            tool_context.state["total_value_found"] = total_value
    
    # Add next questions based on results
    result["next_questions"] = suggest_next_questions(result, hypothesis)
    
    # Check if aggregation failure was detected
    if result.get("aggregation_failure", False):
        logger.warning("SPARQL aggregation failure detected - suggesting Python fallback")
        # Track failed pattern
        if tool_context:
            failed_patterns = tool_context.state.get("failed_patterns", [])
            failed_patterns.append({"query_type": "COUNT/GROUP BY", "timestamp": datetime.now().isoformat()})
            tool_context.state["failed_patterns"] = failed_patterns
            
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

def suggest_next_questions(result: dict, hypothesis: Optional[str]) -> List[str]:
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
            
        # Based on hypothesis
        if hypothesis:
            if "downtime" in hypothesis.lower():
                suggestions.extend([
                    "What time patterns exist in these downtimes?",
                    "Which equipment has the most frequent issues?",
                    "What's the financial impact of this downtime?"
                ])
            elif "performance" in hypothesis.lower() or "oee" in hypothesis.lower():
                suggestions.extend([
                    "How does performance vary by product?",
                    "What's the gap to world-class 85% OEE?",
                    "Which shifts have better performance?"
                ])
            elif "quality" in hypothesis.lower():
                suggestions.extend([
                    "What's the scrap cost by product?",
                    "Are there patterns in quality issues?",
                    "What's the ROI of improving quality?"
                ])
    
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
discovery_pattern_tool = FunctionTool(get_discovery_pattern)
list_patterns_tool = FunctionTool(list_discovery_patterns)
format_insight_tool = FunctionTool(format_insight)
executive_summary_tool = FunctionTool(create_executive_summary)
python_executor_tool = FunctionTool(execute_python_code)

# Define the root agent for ADK
root_agent = LlmAgent(
    name="discovery_analyst",
    description="Discovery Agent that uncovers optimization opportunities through iterative exploration",
    model=DEFAULT_MODEL,
    instruction=f"""You are a discovery agent that uncovers insights through iterative exploration of data.

{comprehensive_context}

## Discovery Methodology

Follow this approach to uncover valuable insights:

1. **EXPLORE** - Start simple to understand the data landscape
   - Begin with basic queries to see what data exists
   - Check a few examples before diving deep
   - Build mental model of relationships

2. **DISCOVER** - When you find anomalies or patterns, dig deeper
   - If you see unexpected values, investigate why
   - Look for clustering, gaps, or outliers
   - Compare actual performance to benchmarks (e.g., 85% OEE)

3. **QUANTIFY** - Always translate findings to business impact
   - Convert operational metrics to financial value
   - Calculate annual impact (hourly × 24 × 365)
   - Use actual product margins and volumes

4. **RECOMMEND** - Provide specific actions with ROI
   - Suggest concrete next steps
   - Include implementation approach
   - Estimate payback period

## Key Behaviors

- **Start with curiosity**: What patterns might exist in this data?
- **Build incrementally**: Don't try complex queries first
- **Learn from failures**: If COUNT returns IRIs, immediately use the fallback query
- **Track discoveries**: Each finding guides the next question
- **Think like a detective**: Follow clues, test hypotheses
- **Always ask "So what?"**: Every finding must connect to value

## Analysis Patterns

When exploring data, consider these proven patterns:
- **Hidden Capacity**: Gap between current and benchmark performance
- **Temporal Patterns**: Time-based clustering of events
- **Product Impact**: Which products affect performance most
- **Quality Trade-offs**: Balance between quality and cost
- **Root Causes**: Why do problems occur repeatedly

## Technical Notes

- Use mes_ontology_populated: prefix for all entities
- Equipment is abstract - query concrete types: Filler, Packer, Palletizer
- Use FILTER(ISIRI(?var)) for entity variables
- When COUNT() with GROUP BY fails, use provided fallback query + analyze_patterns
- For large results, use retrieve_cached_result(cache_id)

Remember: You're not just executing queries - you're discovering opportunities worth millions.

## Advanced Analysis with Python

When SPARQL queries return large datasets (indicated by cache_id), use execute_python_code for sophisticated analysis:

1. **Start Simple**: First explore the data structure
   - Load data into DataFrame and check shape, columns, and preview
   - Always start with basic exploration before complex analysis

2. **Build Understanding**: Based on what you learn, dig deeper
   - Use describe() for statistical summaries
   - Check data types and missing values
   - Look for patterns in the distribution

3. **Discover Patterns**: Apply increasingly sophisticated analysis
   - Group by dimensions to find clusters
   - Look for temporal patterns and anomalies
   - Calculate correlations between metrics

4. **Quantify Impact**: Always connect findings to business value
   - Convert operational metrics to financial impact
   - Calculate annual projections
   - Estimate ROI of improvements

Remember: If code fails, learn from the error and try a different approach. Build your analysis iteratively.""",
    tools=[
        sparql_tool,
        roi_tool,
        visualization_tool,
        analyze_tool,
        cached_result_tool,
        discovery_pattern_tool,
        list_patterns_tool,
        format_insight_tool,
        executive_summary_tool,
        python_executor_tool
    ],
    output_key="latest_discovery"  # Auto-save insights to state
)