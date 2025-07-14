"""
Safe Orchestrator Agent with cost monitoring and token tracking.
Extends the base orchestrator with Vertex AI cost controls.
"""
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from google.adk.agents import LlmAgent
from google.adk.tools import BaseTool

from ..config.settings import DEFAULT_MODEL, DEFAULT_TEMPERATURE
from ..config.prompts.system_prompts import ORCHESTRATOR_PROMPT
from ..utils.vertex_ai_monitor import SafeVertexAIClient, TokenCounter


class SafeOrchestratorSession:
    """Orchestrator session with integrated cost monitoring."""
    
    def __init__(self, 
                 orchestrator: LlmAgent,
                 daily_request_limit: int = 1000,
                 daily_cost_limit: float = 10.0,
                 enable_cost_tracking: bool = True):
        """
        Initialize safe orchestrator session.
        
        Args:
            orchestrator: The base orchestrator agent
            daily_request_limit: Maximum requests per day
            daily_cost_limit: Maximum cost per day in USD
            enable_cost_tracking: Whether to enable cost tracking
        """
        self.orchestrator = orchestrator
        self.enable_cost_tracking = enable_cost_tracking
        
        # Initialize safe client if cost tracking is enabled
        if enable_cost_tracking:
            self.safe_client = SafeVertexAIClient(
                model_name=DEFAULT_MODEL,
                daily_request_limit=daily_request_limit,
                daily_cost_limit=daily_cost_limit,
                hourly_request_limit=max(100, daily_request_limit // 10)
            )
            self.token_counter = TokenCounter(DEFAULT_MODEL)
        else:
            self.safe_client = None
            self.token_counter = None
        
        # Session tracking
        self.discovered_patterns = []
        self.query_history = []
        self.financial_opportunities = []
        self.insights = []
        self.cost_history = []
        self.session_start = pd.Timestamp.now()
    
    def pre_flight_check(self, query: str) -> Dict[str, Any]:
        """
        Perform pre-flight cost estimation before processing a query.
        
        Args:
            query: The user query to process
            
        Returns:
            Dictionary with cost estimate and approval status
        """
        if not self.enable_cost_tracking:
            return {"approved": True, "message": "Cost tracking disabled"}
        
        # Estimate tokens for the query plus expected context
        # Include system prompt and potential tool calls
        full_context = f"{ORCHESTRATOR_PROMPT}\n\nUser Query: {query}\n\n"
        
        # Estimate cost
        cost_estimate = self.token_counter.estimate_cost(
            full_context,
            expected_output_ratio=2.0  # Expect 2x output for analysis tasks
        )
        
        # Check current usage
        usage = self.safe_client.get_usage_summary()
        remaining = self.safe_client.estimate_remaining_requests()
        
        # Determine if we should proceed
        estimated_total = usage["daily"]["cost"] + cost_estimate["estimated_total_cost"]
        approved = (
            remaining["effective"] > 0 and 
            estimated_total < usage["daily"]["limit_cost"]
        )
        
        return {
            "approved": approved,
            "cost_estimate": cost_estimate,
            "current_usage": usage,
            "remaining_requests": remaining,
            "message": "Ready to process" if approved else "Cost or request limits would be exceeded"
        }
    
    def track_request(self, 
                     query: str,
                     response: Any,
                     metadata: Dict[str, Any]):
        """Track a completed request with cost information."""
        if self.enable_cost_tracking and metadata:
            self.cost_history.append({
                "timestamp": pd.Timestamp.now(),
                "query": query[:100] + "..." if len(query) > 100 else query,
                "input_tokens": metadata.get("input_tokens", 0),
                "output_tokens": metadata.get("output_tokens", 0),
                "cost": metadata.get("actual_cost", 0),
                "response_time": metadata.get("response_time", 0),
                "error": metadata.get("error")
            })
    
    def add_pattern(self, pattern: dict):
        """Record a discovered pattern."""
        self.discovered_patterns.append(pattern)
    
    def add_query(self, query: str, results: dict):
        """Record query history with cost tracking."""
        entry = {
            'query': query,
            'results': results,
            'timestamp': pd.Timestamp.now()
        }
        
        # Add cost info if available
        if self.cost_history:
            latest_cost = self.cost_history[-1]
            entry['cost'] = latest_cost.get('cost', 0)
            entry['tokens'] = {
                'input': latest_cost.get('input_tokens', 0),
                'output': latest_cost.get('output_tokens', 0)
            }
        
        self.query_history.append(entry)
    
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
    
    def get_session_cost(self) -> float:
        """Get total cost for this session."""
        if not self.enable_cost_tracking:
            return 0.0
        return sum(entry.get('cost', 0) for entry in self.cost_history)
    
    def get_cost_per_opportunity(self) -> float:
        """Calculate average cost per opportunity discovered."""
        total_cost = self.get_session_cost()
        num_opportunities = len(self.financial_opportunities)
        
        if num_opportunities == 0:
            return 0.0
        
        return total_cost / num_opportunities
    
    def get_roi_estimate(self) -> Dict[str, Any]:
        """Estimate ROI based on opportunities found vs cost incurred."""
        session_cost = self.get_session_cost()
        total_opportunity = self.get_total_opportunity()
        
        if session_cost == 0:
            roi_ratio = float('inf') if total_opportunity > 0 else 0
        else:
            roi_ratio = total_opportunity / session_cost
        
        return {
            "session_cost": session_cost,
            "total_opportunity_annual": total_opportunity,
            "roi_ratio": roi_ratio,
            "cost_per_opportunity": self.get_cost_per_opportunity(),
            "opportunities_found": len(self.financial_opportunities)
        }
    
    def get_summary(self) -> dict:
        """Get enhanced session summary with cost tracking."""
        base_summary = {
            'patterns_discovered': len(self.discovered_patterns),
            'queries_executed': len(self.query_history),
            'opportunities_found': len(self.financial_opportunities),
            'total_annual_value': self.get_total_opportunity(),
            'top_opportunities': self.financial_opportunities[:3],
            'session_duration': str(pd.Timestamp.now() - self.session_start)
        }
        
        # Add cost tracking if enabled
        if self.enable_cost_tracking:
            usage = self.safe_client.get_usage_summary()
            roi = self.get_roi_estimate()
            
            base_summary.update({
                'cost_tracking': {
                    'session_cost': self.get_session_cost(),
                    'total_requests': len(self.cost_history),
                    'total_input_tokens': sum(e.get('input_tokens', 0) for e in self.cost_history),
                    'total_output_tokens': sum(e.get('output_tokens', 0) for e in self.cost_history),
                    'avg_cost_per_request': self.get_session_cost() / max(1, len(self.cost_history)),
                    'roi_analysis': roi,
                    'daily_usage': usage['daily'],
                    'cost_warnings': self._get_cost_warnings(usage)
                }
            })
        
        return base_summary
    
    def _get_cost_warnings(self, usage: Dict[str, Any]) -> List[str]:
        """Generate warnings based on usage patterns."""
        warnings = []
        daily = usage['daily']
        
        # Check if approaching limits
        if daily['cost'] > daily['limit_cost'] * 0.8:
            warnings.append(f"Approaching daily cost limit: ${daily['cost']:.2f} of ${daily['limit_cost']}")
        
        if daily['requests'] > daily['limit_requests'] * 0.8:
            warnings.append(f"Approaching daily request limit: {daily['requests']} of {daily['limit_requests']}")
        
        # Check error rate
        if daily['errors'] > daily['requests'] * 0.1:
            error_rate = (daily['errors'] / max(1, daily['requests'])) * 100
            warnings.append(f"High error rate: {error_rate:.1f}%")
        
        return warnings
    
    def get_cost_report(self) -> str:
        """Generate a formatted cost report."""
        if not self.enable_cost_tracking:
            return "Cost tracking is disabled"
        
        summary = self.get_summary()
        cost_data = summary.get('cost_tracking', {})
        roi = cost_data.get('roi_analysis', {})
        
        report = f"""
=== ADK Manufacturing Analytics Cost Report ===
Session Duration: {summary['session_duration']}

Opportunities Discovered:
- Total Found: {summary['opportunities_found']}
- Total Annual Value: ${summary['total_annual_value']:,.2f}

Cost Analysis:
- Session Cost: ${cost_data.get('session_cost', 0):.4f}
- Total Requests: {cost_data.get('total_requests', 0)}
- Average Cost/Request: ${cost_data.get('avg_cost_per_request', 0):.4f}
- Input Tokens: {cost_data.get('total_input_tokens', 0):,}
- Output Tokens: {cost_data.get('total_output_tokens', 0):,}

ROI Analysis:
- Cost per Opportunity: ${roi.get('cost_per_opportunity', 0):.4f}
- ROI Ratio: {roi.get('roi_ratio', 0):.1f}x
- Break-even: <1 day (based on annual value)

Daily Usage:
- Requests: {cost_data.get('daily_usage', {}).get('requests', 0)} / {cost_data.get('daily_usage', {}).get('limit_requests', 0)}
- Cost: ${cost_data.get('daily_usage', {}).get('cost', 0):.2f} / ${cost_data.get('daily_usage', {}).get('limit_cost', 0):.2f}
"""
        
        # Add warnings if any
        warnings = cost_data.get('cost_warnings', [])
        if warnings:
            report += "\nWarnings:\n"
            for warning in warnings:
                report += f"- {warning}\n"
        
        return report


def create_safe_orchestrator(sub_agents: List[LlmAgent],
                           enable_cost_tracking: bool = True,
                           daily_cost_limit: float = 10.0) -> SafeOrchestratorSession:
    """
    Create a safe orchestrator with cost monitoring.
    
    Args:
        sub_agents: List of specialized agents
        enable_cost_tracking: Whether to enable cost tracking
        daily_cost_limit: Maximum daily cost in USD
    
    Returns:
        SafeOrchestratorSession with cost controls
    """
    # Create base orchestrator
    orchestrator = LlmAgent(
        name="ManufacturingAnalystOrchestrator",
        model=DEFAULT_MODEL,
        description="Main coordinator for manufacturing analytics with cost monitoring",
        instruction=ORCHESTRATOR_PROMPT,
        sub_agents=sub_agents,
        output_key="analysis_summary",
        generate_content_config={
            "temperature": DEFAULT_TEMPERATURE,
            "top_p": 0.95,
            "max_output_tokens": 2048
        }
    )
    
    # Wrap in safe session
    return SafeOrchestratorSession(
        orchestrator=orchestrator,
        daily_cost_limit=daily_cost_limit,
        enable_cost_tracking=enable_cost_tracking
    )


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Mock sub-agents for testing
    mock_agents = []
    
    # Create safe orchestrator
    safe_session = create_safe_orchestrator(
        sub_agents=mock_agents,
        enable_cost_tracking=True,
        daily_cost_limit=1.0
    )
    
    # Example query
    test_query = "Analyze equipment downtime patterns and identify cost saving opportunities"
    
    # Pre-flight check
    pre_flight = safe_session.pre_flight_check(test_query)
    print("Pre-flight Check:", pre_flight)
    
    if pre_flight["approved"]:
        print("Query approved for processing")
        
        # Simulate processing and track some mock data
        safe_session.add_opportunity({
            "description": "Reduce micro-stops on Line 1",
            "annual_value": 125000
        })
        
        safe_session.add_opportunity({
            "description": "Optimize changeover procedures",
            "annual_value": 85000
        })
        
        # Get cost report
        print("\n" + safe_session.get_cost_report())