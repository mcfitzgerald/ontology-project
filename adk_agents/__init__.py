"""
ADK Manufacturing Analytics Agents
"""
__version__ = "0.1.0"

# Import and expose root_agent for ADK web discovery
# Use enhanced version with context management
from .root_agent import root_agent

__all__ = ['root_agent']