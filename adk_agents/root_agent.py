"""
Root agent definition for ADK web UI.

This module creates and exposes the manufacturing analytics orchestrator
as the root_agent for the ADK web interface.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adk_agents.agents.orchestrator import create_orchestrator
from adk_agents.agents.explorer_agent import create_explorer_agent
from adk_agents.agents.query_agent import create_query_builder_agent
from adk_agents.agents.analyst_agent import create_analyst_agent

# Create sub-agents
explorer = create_explorer_agent()
query_builder = create_query_builder_agent()
analyst = create_analyst_agent()

# Create orchestrator with sub-agents
root_agent = create_orchestrator(
    sub_agents=[explorer, query_builder, analyst]
)

# The ADK web UI looks for 'root_agent' specifically
__all__ = ['root_agent']