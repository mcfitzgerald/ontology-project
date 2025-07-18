"""
ADK Agent entry point following 2025 conventions.

This file is the primary entry point for ADK CLI tools.
It must export a 'root_agent' variable.
"""

# Import the root_agent from app.py
from .app import root_agent

# The root_agent is already configured in app.py
# This file just re-exports it for ADK discovery

__all__ = ['root_agent']