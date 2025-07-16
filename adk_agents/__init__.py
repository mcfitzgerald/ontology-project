"""
ADK Manufacturing Analytics Agents
"""
__version__ = "0.1.0"

# Import and expose root_agent for ADK web discovery
# Using new conversational analysis system
from .app import root_agent

__all__ = ['root_agent']