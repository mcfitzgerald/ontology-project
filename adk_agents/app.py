"""
Simplified ADK agent application with conversational analysis.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from adk_agents.utils.context_loader import ContextLoader
from adk_agents.utils.query_cache import QueryCache
from adk_agents.agents.conversation_orchestrator import ConversationOrchestrator
from adk_agents.agents.sparql_executor import SPARQLExecutor
from adk_agents.tools.sparql_tool import execute_sparql_query
from adk_agents.tools.python_analysis import python_analysis_tool
from adk_agents.config.settings import CONTEXT_DIR, ONTOLOGY_DIR

# Initialize shared components
context_loader = ContextLoader(CONTEXT_DIR, ONTOLOGY_DIR)
query_cache = QueryCache(CONTEXT_DIR)

# Create SPARQL tool
# FunctionTool extracts description from function docstring
sparql_tool = FunctionTool(execute_sparql_query)

# Create agents
sparql_executor_instance = SPARQLExecutor(context_loader, query_cache)
sparql_executor = sparql_executor_instance.create_agent(sparql_tool)

orchestrator_instance = ConversationOrchestrator()
orchestrator = orchestrator_instance.create_agent(sparql_executor, python_analysis_tool)

# Export the main agent
root_agent = orchestrator

print(f"✅ Conversational Analysis System initialized")
print(f"   - Context loaded: TTL mindmap and SPARQL reference")
print(f"   - Query cache: {query_cache.get_stats()}")
print(f"   - Ready for exploratory analysis!")