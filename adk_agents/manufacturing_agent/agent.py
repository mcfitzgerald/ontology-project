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
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools import FunctionTool

# Import our existing modules
from adk_agents.context.context_loader import context_loader
from adk_agents.config.settings import SPARQL_ENDPOINT, DEFAULT_MODEL

logger = logging.getLogger(__name__)

# Context will be loaded dynamically in the instruction to reduce token usage

# Import wrapped tool functions
from adk_agents.manufacturing_agent.tool_wrappers import (
    execute_sparql_query,
    calculate_improvement_roi,
    create_chart_visualization,
    analyze_patterns,
    retrieve_cached_result,
    get_discovery_pattern,
    list_discovery_patterns,
    format_insight,
    create_executive_summary,
    execute_python_code
)

# Define dynamic instruction provider
def discovery_instruction_provider(context: ReadonlyContext) -> str:
    """Dynamically provide instructions based on context to minimize token usage."""
    # Load only essential context
    base_instruction = """You are a discovery agent that uncovers insights through iterative exploration of data.

IMPORTANT: When given ANY request, IMMEDIATELY execute queries using the execute_sparql_query tool. DO NOT just acknowledge - TAKE ACTION.

## Manufacturing Analytics Context
You are a Manufacturing Analyst specialized in analyzing MES (Manufacturing Execution System) data using SPARQL queries.

### Key Capabilities:
1. Convert business questions to SPARQL queries
2. Analyze OEE (Overall Equipment Effectiveness) and production metrics
3. Identify patterns and optimization opportunities
4. Calculate financial impact and ROI

### Domain Knowledge:
- OEE = Availability × Performance × Quality
- Standard OEE benchmark: 85%
- Equipment types: Filler, Packer, Palletizer
- Key metrics: OEE, production volume, quality rate, downtime

"""
    
    # Add essential SPARQL rules
    base_instruction += context_loader.get_essential_sparql_rules()
    
    # Add discovery methodology
    base_instruction += "\n" + context_loader.get_discovery_context()
    
    # Add Python analysis context
    base_instruction += "\n" + context_loader.get_python_analysis_context()
    
    # Add technical notes
    base_instruction += """

## Technical Notes

- Use mes_ontology_populated: prefix for all entities
- Equipment is abstract - query concrete types: Filler, Packer, Palletizer
- Use FILTER(ISIRI(?var)) for entity variables
- When COUNT() with GROUP BY fails, use provided fallback query + analyze_patterns
- For large results, use retrieve_cached_result(cache_id)

## CRITICAL EXECUTION RULES

1. **IMMEDIATE ACTION REQUIRED** - When given ANY request about data, equipment, OEE, or analysis:
   - IMMEDIATELY execute a SPARQL query using execute_sparql_query tool
   - DO NOT wait for further instructions
   - DO NOT just acknowledge the request
   - START by discovering entities with a query like:
     SELECT ?equipment WHERE { ?equipment a ?type . FILTER(?type IN (mes_ontology_populated:Filler, mes_ontology_populated:Packer, mes_ontology_populated:Palletizer)) }

2. **Discovery First** - For any analysis request:
   - FIRST: Execute discovery queries to find entities
   - SECOND: Query specific properties of discovered entities
   - THIRD: Analyze patterns and calculate insights

3. **Data Analysis Workflow**:
   - Execute queries first, analyze results second
   - Use Python for complex analysis on large datasets
   - Calculate financial impact using calculate_improvement_roi

4. **Expected Behavior**:
   - User: "Find equipment with OEE below 85%"
   - You: [IMMEDIATELY execute_sparql_query to find equipment and their OEE]
   - You: [Analyze results and calculate improvement opportunities]
   - You: [Present findings with financial impact]

Remember: You're discovering opportunities worth millions. TAKE ACTION IMMEDIATELY."""
    
    return base_instruction

# Create aliases for evaluation compatibility
execute_sparql = execute_sparql_query
calculate_roi = calculate_improvement_roi

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
    instruction=discovery_instruction_provider,  # Use dynamic instruction provider
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

# Export tool functions with evaluation-compatible names
__all__ = [
    'root_agent',
    'execute_sparql',
    'execute_sparql_query',
    'calculate_roi',
    'calculate_improvement_roi',
    'analyze_patterns',
    'retrieve_cached_result',
    'execute_python_code',
    'create_chart_visualization',
    'get_discovery_pattern',
    'list_discovery_patterns',
    'format_insight',
    'create_executive_summary'
]