"""
Analyst Agent - Performs statistical analysis and financial modeling.
"""
from google.adk.agents import LlmAgent

from ..config.settings import DEFAULT_MODEL, DEFAULT_TEMPERATURE
from ..config.prompts.system_prompts import ANALYST_PROMPT
from ..tools.analysis_tools import (
    temporal_analysis_tool,
    financial_modeling_tool,
    anomaly_detection_tool
)


def create_analyst_agent() -> LlmAgent:
    """
    Create the data analyst agent.
    
    Returns:
        Configured analyst LlmAgent
    """
    analyst = LlmAgent(
        name="DataAnalyst",
        model=DEFAULT_MODEL,
        description="Performs statistical analysis, pattern recognition, and financial modeling on manufacturing data",
        instruction=ANALYST_PROMPT,
        tools=[
            temporal_analysis_tool,
            financial_modeling_tool,
            anomaly_detection_tool
        ],
        output_key="analysis_findings",
        generate_content_config={
            "temperature": DEFAULT_TEMPERATURE,
            "top_p": 0.95,
            "max_output_tokens": 2048
        }
    )
    
    return analyst