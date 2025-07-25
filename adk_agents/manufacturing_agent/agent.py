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
    retrieve_cached_result,
    execute_python_code
)

# Define dynamic instruction provider
def discovery_instruction_provider(context: ReadonlyContext) -> str:
    """Dynamically provide instructions based on analysis phase.
    
    This function loads context progressively based on the current phase
    of analysis, significantly reducing token usage for simple queries.
    """
    # Check what phase we're in based on state
    phase = context.state.get('analysis_phase', 'initial') if context.state else 'initial'
    
    logger.debug(f"Loading context for phase: {phase}")
    
    if phase == 'initial':
        # Load: system_prompt + data_catalogue + mindmap
        return context_loader.get_initial_context()
    elif phase == 'sparql_construction':
        # Add: sparql_ref + query_patterns
        return context_loader.get_sparql_context()
    elif phase == 'python_analysis':
        # Add: python_analysis guide
        return context_loader.get_python_context()
    else:
        # Fallback to comprehensive context
        return context_loader.get_comprehensive_agent_context()

# Create aliases for evaluation compatibility
execute_sparql = execute_sparql_query

# Create FunctionTool instances
sparql_tool = FunctionTool(execute_sparql_query)
cached_result_tool = FunctionTool(retrieve_cached_result)
python_executor_tool = FunctionTool(execute_python_code)

# Define the root agent for ADK
root_agent = LlmAgent(
    name="collaborative_analyst",
    description="Collaborative Manufacturing Analyst that helps users explore data through guided conversation",
    model=DEFAULT_MODEL,
    instruction=discovery_instruction_provider,  # Use dynamic instruction provider
    tools=[
        sparql_tool,
        cached_result_tool,
        python_executor_tool
    ],
    output_key="latest_discovery"  # Auto-save insights to state
)

# Export tool functions with evaluation-compatible names
__all__ = [
    'root_agent',
    'execute_sparql',
    'execute_sparql_query',
    'retrieve_cached_result',
    'execute_python_code'
]