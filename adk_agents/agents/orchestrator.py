"""
Orchestrator Agent - Main coordinator for manufacturing analytics conversations.
"""
from typing import List, Optional
import pandas as pd
from google.adk.agents import LlmAgent
from google.adk.tools import BaseTool

from ..config.settings import DEFAULT_MODEL, DEFAULT_TEMPERATURE
from ..config.prompts.system_prompts import ORCHESTRATOR_PROMPT


def create_orchestrator(sub_agents: List[LlmAgent]) -> LlmAgent:
    """
    Create the main orchestrator agent.
    
    Args:
        sub_agents: List of specialized agents (explorer, query_builder, analyst)
    
    Returns:
        Configured orchestrator LlmAgent
    """
    orchestrator = LlmAgent(
        name="ManufacturingAnalystOrchestrator",
        model=DEFAULT_MODEL,
        description="Main coordinator for manufacturing analytics that discovers business value through data exploration",
        instruction=ORCHESTRATOR_PROMPT,
        sub_agents=sub_agents,
        output_key="analysis_summary",
        generate_content_config={
            "temperature": DEFAULT_TEMPERATURE,
            "top_p": 0.95,
            "max_output_tokens": 2048
        }
    )
    
    return orchestrator


class OrchestratorSession:
    """Manages the orchestrator session and discovered insights."""
    
    def __init__(self, orchestrator: LlmAgent):
        self.orchestrator = orchestrator
        self.discovered_patterns = []
        self.query_history = []
        self.financial_opportunities = []
        self.insights = []
    
    def add_pattern(self, pattern: dict):
        """Record a discovered pattern."""
        self.discovered_patterns.append(pattern)
    
    def add_query(self, query: str, results: dict):
        """Record query history."""
        self.query_history.append({
            'query': query,
            'results': results,
            'timestamp': pd.Timestamp.now()
        })
    
    def add_opportunity(self, opportunity: dict):
        """Record a financial opportunity."""
        self.financial_opportunities.append(opportunity)
        # Sort by value
        self.financial_opportunities.sort(
            key=lambda x: x.get('annual_value', 0), 
            reverse=True
        )
    
    def get_total_opportunity(self) -> float:
        """Calculate total discovered opportunity value."""
        return sum(opp.get('annual_value', 0) 
                  for opp in self.financial_opportunities)
    
    def get_summary(self) -> dict:
        """Get session summary."""
        return {
            'patterns_discovered': len(self.discovered_patterns),
            'queries_executed': len(self.query_history),
            'opportunities_found': len(self.financial_opportunities),
            'total_annual_value': self.get_total_opportunity(),
            'top_opportunities': self.financial_opportunities[:3]
        }