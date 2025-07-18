"""
ADK-integrated agent application following 2025 patterns.

This module follows the ADK 2025 conventions:
- Exports a 'root_agent' variable for discovery by ADK tools
- Uses FunctionTool for wrapping functions
- Relies on ADK framework for session/artifact management via CLI
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Google ADK imports - 2025 structure
from google.adk.agents import Agent, LlmAgent
from google.adk.tools import FunctionTool

from adk_agents.utils.ontology_knowledge import OntologyKnowledge
from adk_agents.agents.conversation_orchestrator import ConversationOrchestrator
from adk_agents.agents.sparql_executor import SPARQLExecutor
from adk_agents.tools.sparql_tool import execute_sparql_query
from adk_agents.tools.python_analysis import python_analysis_tool
from adk_agents.config.settings import CONTEXT_DIR, ONTOLOGY_DIR

# Initialize knowledge base
ontology_knowledge = OntologyKnowledge()

# Create SPARQL tool
# FunctionTool extracts description from function docstring
sparql_tool = FunctionTool(execute_sparql_query)

# Create agents
sparql_executor = SPARQLExecutor().create_agent(sparql_tool)
orchestrator = ConversationOrchestrator(ontology_knowledge).create_agent(
    sparql_executor, 
    python_analysis_tool
)

# REQUIRED: Export as 'root_agent' for ADK discovery
# This is the convention that ADK CLI tools (adk web, adk run) look for
root_agent = orchestrator

# Optional: Print initialization status
if __name__ == "__main__":
    print(f"✅ ADK-Integrated Analysis System initialized")
    print(f"   - Ontology knowledge loaded and cached")
    print(f"   - To run: Use 'adk web' or 'adk run' from the parent directory")
    print(f"   - Session/artifact services are managed by ADK framework")