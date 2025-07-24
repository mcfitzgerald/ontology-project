"""Manufacturing Agent for ADK Web UI."""
from .agent import root_agent

# ADK eval expects 'agent' module
agent = root_agent

__all__ = ['root_agent', 'agent']