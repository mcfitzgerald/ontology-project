"""
Utilities for managing ADK session state effectively.
"""
from typing import Dict, Any, List
import time
from google.adk.tools import ToolContext

class StateManager:
    """Helper for organized state management."""
    
    @staticmethod
    def track_finding(tool_context: ToolContext, finding: Dict[str, Any]):
        """Track important findings in state."""
        findings = tool_context.state.get("key_findings", [])
        findings.append({
            **finding,
            "timestamp": time.time()
        })
        # Keep most recent 20 findings
        tool_context.state["key_findings"] = findings[-20:]
    
    @staticmethod
    def record_query_pattern(tool_context: ToolContext, query: str, success: bool):
        """Record successful query patterns for reuse."""
        if success:
            patterns = tool_context.state.get("app:successful_patterns", [])
            patterns.append({
                "query": query,
                "timestamp": time.time()
            })
            # App-level state shared across sessions
            tool_context.state["app:successful_patterns"] = patterns[-50:]
    
    @staticmethod
    def get_analysis_context(tool_context: ToolContext) -> Dict[str, Any]:
        """Get current analysis context from state."""
        return {
            "phase": tool_context.state.get("analysis_phase", "discovery"),
            "focus": tool_context.state.get("analysis_focus", "general"),
            "findings_count": len(tool_context.state.get("key_findings", [])),
            "queries_executed": tool_context.state.get("query_count", 0)
        }