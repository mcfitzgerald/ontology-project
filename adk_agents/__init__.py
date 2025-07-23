"""ADK Manufacturing Analytics Agent System."""
__version__ = "0.1.0"

# Import the root_agent for ADK Web UI
from .manufacturing_agent import root_agent

# CLI agent imports
from .agents.manufacturing_analyst import ManufacturingAnalystAgent, create_manufacturing_analyst
from .tools.sparql_tool import execute_sparql
from .tools.analysis_tools import analyze_patterns, calculate_roi
from .tools.cache_manager import cache_manager

__all__ = [
    "root_agent",  # For ADK Web UI
    "ManufacturingAnalystAgent",
    "create_manufacturing_analyst",
    "execute_sparql", 
    "analyze_patterns",
    "calculate_roi",
    "cache_manager"
]