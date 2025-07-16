"""
Explorer Agent - Discovers ontology structure and business context.
"""
from google.adk.agents import LlmAgent

from ..config.settings import DEFAULT_MODEL, DEFAULT_TEMPERATURE
from ..config.prompts.system_prompts import EXPLORER_PROMPT
from ..tools.ontology_tool import ontology_explorer_tool, get_context_tool
from ..tools.sparql_tool import (
    sparql_tool,
    discover_classes,
    discover_equipment_instances,
    discover_properties_for_class,
    discover_entity_properties,
    validate_entity_exists
)
from google.adk.tools import FunctionTool


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
        tools=[
            ontology_explorer_tool,
            get_context_tool,
            sparql_tool,
            FunctionTool(discover_classes),
            FunctionTool(discover_equipment_instances),
            FunctionTool(discover_properties_for_class),
            FunctionTool(discover_entity_properties),
            FunctionTool(validate_entity_exists)
        ],
        output_key="ontology_insights",
        generate_content_config={
            "temperature": DEFAULT_TEMPERATURE,
            "top_p": 0.95,
            "max_output_tokens": 1024
        }
    )
    
    return explorer