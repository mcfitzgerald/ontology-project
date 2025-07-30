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
    """Always provide comprehensive instructions.
    
    This function loads all context upfront to ensure the agent has
    complete information for SPARQL queries and analysis.
    """
    import time
    
    logger.debug("Loading comprehensive context")
    
    # Always load comprehensive context
    base_context = context_loader.get_comprehensive_agent_context()
    
    # Add session freshness monitoring
    session_notes = []
    
    # Check session age (if we have access to session info through state)
    session_start_time = context.state.get('session_start_time', time.time()) if context.state else time.time()
    session_age_hours = (time.time() - session_start_time) / 3600
    
    if session_age_hours > 24:
        session_notes.append(
            "\nNOTE: This session is over 24 hours old. Consider suggesting a fresh session "
            "after summarizing key findings to maintain optimal performance."
        )
    elif session_age_hours > 2:
        # Check for inactivity
        last_activity = context.state.get('last_activity_time', time.time()) if context.state else time.time()
        inactivity_hours = (time.time() - last_activity) / 3600
        if inactivity_hours > 2:
            session_notes.append(
                f"\nNOTE: User has been inactive for {inactivity_hours:.1f} hours. "
                "They may benefit from a quick recap or a fresh session."
            )
    
    # Check event count (approximation based on state entries)
    if context.state:
        state_entries = len(context.state)
        if state_entries > 50:  # Rough proxy for conversation length
            session_notes.append(
                "\nNOTE: This conversation has many state entries. If it becomes unwieldy, "
                "suggest starting a fresh session with a summary of findings."
            )
    
    # Combine base context with session notes
    if session_notes:
        return base_context + "\n\n## Session Status" + "".join(session_notes)
    else:
        return base_context

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