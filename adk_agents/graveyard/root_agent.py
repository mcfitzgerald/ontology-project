"""
Enhanced root agent with improved context management and query optimization.

This module creates the enhanced manufacturing analytics orchestrator
with shared context and performance monitoring.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adk_agents.agents.enhanced.orchestrator_enhanced import (
    create_enhanced_orchestrator,
    create_explorer_agent_with_enhancements,
    create_query_builder_with_enhancements
)
from adk_agents.agents.analyst_agent import create_analyst_agent

# Create enhanced sub-agents
explorer = create_explorer_agent_with_enhancements()
query_builder = create_query_builder_with_enhancements()
analyst = create_analyst_agent()

# Create enhanced orchestrator with sub-agents
root_agent = create_enhanced_orchestrator(
    sub_agents=[explorer, query_builder, analyst]
)

# The ADK web UI looks for 'root_agent' specifically
__all__ = ['root_agent']