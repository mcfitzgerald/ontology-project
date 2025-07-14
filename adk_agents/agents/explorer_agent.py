"""
Explorer Agent - Discovers ontology structure and business context.
"""
from google.adk.agents import LlmAgent

from ..config.settings import DEFAULT_MODEL, DEFAULT_TEMPERATURE
from ..config.prompts.system_prompts import EXPLORER_PROMPT
from ..tools.ontology_tool import ontology_explorer_tool, get_context_tool


def create_explorer_agent() -> LlmAgent:
    """
    Create the ontology explorer agent.
    
    Returns:
        Configured explorer LlmAgent
    """
    explorer = LlmAgent(
        name="OntologyExplorer",
        model=DEFAULT_MODEL,
        description="Explores ontology structure to understand available data and business context",
        instruction=EXPLORER_PROMPT,
        tools=[ontology_explorer_tool, get_context_tool],
        output_key="ontology_insights",
        generate_content_config={
            "temperature": DEFAULT_TEMPERATURE,
            "top_p": 0.95,
            "max_output_tokens": 1024
        }
    )
    
    return explorer