"""
SPARQL Executor Agent - Pure query execution with Owlready2 rules.
"""
from typing import Dict, Any, List
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from ..config.settings import DEFAULT_MODEL

class SPARQLExecutor:
    """Handles SPARQL query execution with minimal context."""
    
    def __init__(self):
        """Initialize without dependencies."""
        pass
    
    def get_system_prompt(self) -> str:
        """Minimal prompt focused on query execution."""
        return """You execute SPARQL queries for the MES ontology using Owlready2.

Critical Rules:
- ALWAYS use mes_ontology_populated: prefix for all properties/classes
- NO angle brackets in queries
- NO PREFIX declarations
- Use FILTER(ISIRI()) for entity filtering
- Timestamps are literals, not IRIs

Error Recovery:
- "Unknown prefix" → Add mes_ontology_populated:
- "Lexing error" → Remove angle brackets
- "No results" → Verify property names
- Timeout → Add LIMIT clause

Execute queries efficiently and explain any errors encountered."""
    
    def create_agent(self, sparql_tool: FunctionTool) -> LlmAgent:
        """Create the SPARQL executor agent."""
        return LlmAgent(
            name="SPARQLExecutor",
            model=DEFAULT_MODEL,
            instruction=self.get_system_prompt(),
            description="Executes SPARQL queries with Owlready2 compliance",
            tools=[sparql_tool]
        )