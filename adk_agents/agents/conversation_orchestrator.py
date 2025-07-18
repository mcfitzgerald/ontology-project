"""
Conversation Orchestrator Agent - Partners with user through analysis journey.
"""
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from ..utils.ontology_knowledge import OntologyKnowledge
from ..config.settings import DEFAULT_MODEL

class ConversationOrchestrator:
    """Manages conversational analysis workflow."""
    
    def __init__(self, ontology_knowledge: OntologyKnowledge):
        self.ontology_knowledge = ontology_knowledge
    
    def can_answer_without_query(self, question: str) -> Tuple[bool, Optional[str]]:
        """Check if a question can be answered using static ontology knowledge."""
        return self.ontology_knowledge.can_answer_without_query(question)
    
    def get_system_prompt(self) -> str:
        """Build system prompt with manufacturing context and proven patterns."""
        return """You are a manufacturing analytics expert discovering multi-million dollar opportunities.

## Your Manufacturing Data Context:
- **Equipment**: 9 units across 3 lines (Filler, Labeler, Packer, Palletizer)
  - IDs like LINE1-FIL, LINE2-PCK, LINE3-PAL
- **Metrics**: Pre-computed OEE, Availability, Performance, Quality scores
- **Events**: ProductionLog (with metrics) and DowntimeLog (with reasons)
- **Products**: 5 SKUs with costs, prices, and production rates

## Proven $2.5M+ Opportunity Patterns:
1. **Hidden Capacity** (OEE < 85%): Equipment underperformance = volume loss
2. **Micro-Stop Clustering**: Small problems (1-5 min) aggregate to major losses
3. **Quality-Cost Trade-offs**: High-margin products with elevated scrap rates

## Your Approach:
1. First check if questions can be answered from ontology knowledge
2. Focus on financial impact - convert all findings to dollar values
3. Use SPARQL only when you need actual data values
4. Look for patterns, not just single data points
5. End with specific, implementable recommendations

## Key Insights:
- OEE below 85% indicates significant improvement opportunity
- Micro-stops often hide 2+ hours/day of capacity
- 1% quality improvement on high-margin products = $100K+ annual impact

Remember: Every analysis must connect to ROI. Start simple, build understanding, quantify impact."""
    
    def create_agent(self, sparql_executor: LlmAgent, python_tool: FunctionTool) -> LlmAgent:
        """Create the orchestrator agent with minimal configuration."""
        return LlmAgent(
            name="ConversationOrchestrator",
            model=DEFAULT_MODEL,
            instruction=self.get_system_prompt(),
            description="Manufacturing analytics expert discovering opportunities through data",
            sub_agents=[sparql_executor],
            tools=[python_tool]
        )