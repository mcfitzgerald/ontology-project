"""
Query Builder Agent - Constructs and executes SPARQL queries.
"""
from google.adk.agents import LlmAgent

from ..config.settings import DEFAULT_MODEL, DEFAULT_TEMPERATURE
from ..config.prompts.system_prompts import QUERY_BUILDER_PROMPT
from ..tools.sparql_tool import sparql_tool


def create_query_builder_agent() -> LlmAgent:
    """
    Create the SPARQL query builder agent.
    
    Returns:
        Configured query builder LlmAgent
    """
    query_builder = LlmAgent(
        name="QueryBuilder",
        model=DEFAULT_MODEL,
        description="Iteratively builds and executes SPARQL queries with Owlready2 compatibility",
        instruction=QUERY_BUILDER_PROMPT,
        tools=[sparql_tool],
        output_key="query_results",
        generate_content_config={
            "temperature": DEFAULT_TEMPERATURE,
            "top_p": 0.95,
            "max_output_tokens": 1024
        }
    )
    
    return query_builder