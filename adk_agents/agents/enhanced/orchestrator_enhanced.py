"""
Enhanced Orchestrator Agent with improved context management and performance monitoring.
"""
from typing import List, Optional, Dict, Any, Callable
from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext

from ...context.shared_context import SharedAgentContext
from ...config.settings import DEFAULT_MODEL, DEFAULT_TEMPERATURE
from google.adk.tools import FunctionTool


def create_enhanced_orchestrator(sub_agents: List[LlmAgent]) -> LlmAgent:
    """
    Create the enhanced orchestrator agent with context management.
    
    Args:
        sub_agents: List of specialized agents
    
    Returns:
        Configured orchestrator LlmAgent
    """
    
    def context_aware_instruction(context: ReadonlyContext) -> str:
        """Generate dynamic instruction based on current context"""
        # Load shared context from state
        shared_context = SharedAgentContext.from_state(context.state)
        
        base_instruction = """
        You are the lead manufacturing analyst coordinating an investigation.
        
        You have access to shared context including:
        - Discovered properties: {property_count} classes explored
        - Cached query results: {query_count} successful queries
        - Known issues: {issue_count} documented workarounds
        - Successful query patterns: {pattern_count} patterns available
        
        Your role is to:
        1. Check shared context before delegating exploration tasks
        2. Update shared context with new discoveries
        3. Use known workarounds for common issues
        4. Maintain analysis momentum by reusing successful patterns
        5. Focus on business value - every analysis must connect to financial impact
        
        Key principles:
        - Always check cached results before making new queries
        - Learn from failed queries to avoid repeating mistakes
        - Build on successful patterns
        - Quantify everything - convert operational metrics to financial impact
        - End with specific, implementable recommendations
        
        Available sub-agents:
        - OntologyExplorer: Discovers available data and relationships
        - QueryBuilder: Constructs and executes SPARQL queries iteratively
        - DataAnalyst: Performs statistical and financial analysis
        
        Recent successful patterns:
        {recent_patterns}
        
        Known issues to avoid:
        {known_issues}
        """
        
        # Format recent patterns
        patterns = shared_context.get_query_patterns()
        recent_patterns = "\n".join([
            f"- {p['purpose']}: {p['row_count']} results"
            for p in patterns[:5]
        ]) if patterns else "None yet"
        
        # Format known issues
        issues = shared_context.known_issues[-3:]
        known_issues = "\n".join([
            f"- {issue['type']}: {issue['workaround']}"
            for issue in issues
        ]) if issues else "None yet"
        
        return base_instruction.format(
            property_count=len(shared_context.discovered_properties),
            query_count=len(shared_context.query_results),
            issue_count=len(shared_context.known_issues),
            pattern_count=len(patterns),
            recent_patterns=recent_patterns,
            known_issues=known_issues
        )
    
    orchestrator = LlmAgent(
        name="EnhancedManufacturingOrchestrator",
        model=DEFAULT_MODEL,
        description="Enhanced coordinator with shared context management",
        instruction=context_aware_instruction,
        sub_agents=sub_agents,
        output_key="analysis_summary",
        tools=[],  # Transfer is handled by sub_agents parameter
        generate_content_config={
            "temperature": DEFAULT_TEMPERATURE,
            "top_p": 0.95,
            "max_output_tokens": 2048
        }
    )
    
    return orchestrator


def get_orchestrator_with_monitoring() -> LlmAgent:
    """Get orchestrator with performance monitoring callbacks"""
    from ..explorer_agent import create_explorer_agent
    from ..query_agent import create_query_builder_agent
    from ..analyst_agent import create_analyst_agent
    
    # Create enhanced sub-agents
    explorer = create_explorer_agent_with_enhancements()
    query_builder = create_query_builder_with_enhancements()
    analyst = create_analyst_agent()
    
    return create_enhanced_orchestrator([explorer, query_builder, analyst])


def create_explorer_agent_with_enhancements() -> LlmAgent:
    """Create explorer agent with enhanced query tools"""
    from ..explorer_agent import create_explorer_agent
    from ...tools.sparql_tool import (
        query_downtime_pareto,
        query_time_series_downtime,
        query_oee_analysis,
        query_defect_analysis
    )
    from google.adk.tools import FunctionTool
    
    base_explorer = create_explorer_agent()
    
    # Add new optimized query tools
    if hasattr(base_explorer, 'tools') and isinstance(base_explorer.tools, list):
        base_explorer.tools.extend([
            FunctionTool(query_downtime_pareto),
            FunctionTool(query_time_series_downtime),
            FunctionTool(query_oee_analysis),
            FunctionTool(query_defect_analysis)
        ])
    
    return base_explorer


def create_query_builder_with_enhancements() -> LlmAgent:
    """Create query builder with progressive query tool"""
    from ..query_agent import create_query_builder_agent
    from ...tools.sparql_tool import build_progressive_query
    from google.adk.tools import FunctionTool
    
    base_builder = create_query_builder_agent()
    
    # Add progressive query building tool
    if hasattr(base_builder, 'tools') and isinstance(base_builder.tools, list):
        base_builder.tools.append(FunctionTool(build_progressive_query))
    
    return base_builder