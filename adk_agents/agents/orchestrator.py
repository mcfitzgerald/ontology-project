"""
Orchestrator Agent - Main coordinator for manufacturing analytics conversations.
"""
from typing import List, Optional, Dict, Any
import pandas as pd
import logging
from google.adk.agents import LlmAgent
from google.adk.tools import BaseTool

from ..config.settings import DEFAULT_MODEL, DEFAULT_TEMPERATURE
from ..config.prompts.system_prompts import ORCHESTRATOR_PROMPT

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SharedContext:
    """Shared context that agents can learn from."""
    
    def __init__(self):
        self.discovered_entities: Dict[str, List[str]] = {
            'equipment': [],
            'products': [],
            'properties': {},
            'relationships': []
        }
        self.successful_queries: List[Dict[str, Any]] = []
        self.failed_queries: List[Dict[str, Any]] = []
        self.validated_patterns: List[str] = []
        self.business_insights: List[Dict[str, Any]] = []
    
    def add_discovered_entity(self, entity_type: str, entity: str):
        """Add a discovered entity."""
        if entity_type in self.discovered_entities:
            if entity not in self.discovered_entities[entity_type]:
                self.discovered_entities[entity_type].append(entity)
                logger.info(f"Discovered {entity_type}: {entity}")
    
    def add_successful_query(self, query: str, results: Any, purpose: str = ""):
        """Record a successful query for reuse."""
        self.successful_queries.append({
            'query': query,
            'results': results,
            'purpose': purpose,
            'timestamp': pd.Timestamp.now()
        })
        logger.info(f"Successful query recorded: {purpose}")
    
    def add_failed_query(self, query: str, error: str):
        """Record a failed query to avoid repeating mistakes."""
        self.failed_queries.append({
            'query': query,
            'error': error,
            'timestamp': pd.Timestamp.now()
        })
        logger.warning(f"Failed query recorded: {error}")
    
    def add_validated_pattern(self, pattern: str):
        """Add a validated SPARQL pattern that works."""
        if pattern not in self.validated_patterns:
            self.validated_patterns.append(pattern)
            logger.info(f"Validated pattern: {pattern}")
    
    def add_business_insight(self, insight: Dict[str, Any]):
        """Record a business insight discovered."""
        self.business_insights.append({
            **insight,
            'timestamp': pd.Timestamp.now()
        })
        logger.info(f"Business insight: {insight.get('description', 'New insight')}")
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of discovered context."""
        return {
            'entities_discovered': {k: len(v) for k, v in self.discovered_entities.items()},
            'successful_queries': len(self.successful_queries),
            'failed_queries': len(self.failed_queries),
            'validated_patterns': len(self.validated_patterns),
            'business_insights': len(self.business_insights),
            'sample_entities': {
                k: v[:3] for k, v in self.discovered_entities.items() if v
            }
        }


# Global shared context instance
shared_context = SharedContext()


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