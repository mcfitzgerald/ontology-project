"""Insight formatter tool for creating executive-ready recommendations."""
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

def format_insight(
    finding: str,
    evidence: Dict[str, Any],
    impact: float,
    action: str,
    confidence: float = 0.8,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """Format a discovery into an executive-ready insight.
    
    Args:
        finding: The key discovery or insight
        evidence: Data supporting the finding (queries, metrics, patterns)
        impact: Annual financial impact in dollars
        action: Recommended action to capture the opportunity
        confidence: Confidence level (0-1) in the finding
        tool_context: ADK tool context for state management
        
    Returns:
        Formatted insight with all details
    """
    # Generate implementation steps based on action
    implementation_steps = generate_implementation_steps(action)
    
    # Define success metrics
    success_metrics = define_success_metrics(finding, impact)
    
    # Calculate payback period (assuming 20% of impact as implementation cost)
    implementation_cost = impact * 0.2
    if impact > 0:
        payback_months = round((implementation_cost / impact) * 12, 1)
    else:
        payback_months = 0
    
    insight = {
        "insight": finding,
        "evidence": evidence,
        "annual_impact": f"${impact:,.0f}",
        "confidence": f"{confidence:.0%}",
        "recommended_action": action,
        "implementation_steps": implementation_steps,
        "success_metrics": success_metrics,
        "payback_period": f"{payback_months} months",
        "priority": calculate_priority(impact, confidence, payback_months),
        "timestamp": datetime.now().isoformat()
    }
    
    # Track in state
    if tool_context:
        insights = tool_context.state.get("formatted_insights", [])
        insights.append(insight)
        tool_context.state["formatted_insights"] = insights
        
        # Update total value found
        total_value = tool_context.state.get("total_value_found", 0)
        tool_context.state["total_value_found"] = total_value + impact
    
    return insight

def generate_implementation_steps(action: str) -> List[str]:
    """Generate implementation steps based on the recommended action."""
    action_lower = action.lower()
    
    if "sensor" in action_lower or "adjustment" in action_lower:
        return [
            "1. Conduct detailed root cause analysis during next downtime",
            "2. Check sensor calibration and alignment",
            "3. Adjust mechanical guides and clearances",
            "4. Implement monitoring to track improvements",
            "5. Document settings for future reference"
        ]
    elif "maintenance" in action_lower or "preventive" in action_lower:
        return [
            "1. Analyze failure patterns to optimize PM schedule",
            "2. Create checklist for high-risk components",
            "3. Train maintenance team on early warning signs",
            "4. Implement predictive maintenance triggers",
            "5. Track MTBF improvements"
        ]
    elif "quality" in action_lower or "inspection" in action_lower:
        return [
            "1. Audit current quality control process",
            "2. Identify critical control points",
            "3. Implement enhanced inspection at key stages",
            "4. Train operators on quality standards",
            "5. Monitor scrap rate reduction"
        ]
    elif "training" in action_lower or "operator" in action_lower:
        return [
            "1. Identify skill gaps through observation",
            "2. Develop targeted training modules",
            "3. Implement buddy system for knowledge transfer",
            "4. Create visual work instructions",
            "5. Track performance improvements by operator"
        ]
    elif "product" in action_lower or "schedule" in action_lower:
        return [
            "1. Analyze product performance data",
            "2. Optimize production sequence",
            "3. Batch similar products together",
            "4. Minimize changeovers for problem SKUs",
            "5. Track OEE by product mix"
        ]
    else:
        return [
            "1. Form cross-functional improvement team",
            "2. Develop detailed implementation plan",
            "3. Run pilot test on single line/shift",
            "4. Measure results and refine approach",
            "5. Roll out to all affected areas"
        ]

def define_success_metrics(finding: str, impact: float) -> List[str]:
    """Define success metrics based on the finding type."""
    finding_lower = finding.lower()
    
    metrics = []
    
    # Always include financial metric
    metrics.append(f"Achieve ${impact/12:,.0f} monthly savings within 3 months")
    
    # Add specific metrics based on finding type
    if "downtime" in finding_lower or "availability" in finding_lower:
        metrics.extend([
            "Reduce unplanned downtime by 50%",
            "Improve availability score to >90%",
            "Decrease MTTR by 30%"
        ])
    elif "performance" in finding_lower or "oee" in finding_lower:
        metrics.extend([
            "Increase OEE to 85% benchmark",
            "Improve performance score by 10 points",
            "Reduce micro-stops by 60%"
        ])
    elif "quality" in finding_lower or "scrap" in finding_lower:
        metrics.extend([
            "Reduce scrap rate to <1%",
            "Improve first-pass quality to 99%",
            "Decrease customer complaints by 50%"
        ])
    else:
        metrics.extend([
            "Achieve target KPI within 90 days",
            "Sustain improvements for 6 months",
            "Document and standardize new process"
        ])
    
    return metrics

def calculate_priority(impact: float, confidence: float, payback_months: float) -> str:
    """Calculate priority based on impact, confidence, and payback period."""
    # Score based on impact (normalized to 0-100)
    impact_score = min(impact / 10000, 100)  # $1M = 100 score
    
    # Confidence factor
    confidence_score = confidence * 100
    
    # Payback factor (faster = better)
    payback_score = max(0, 100 - (payback_months * 5))  # 20 months = 0 score
    
    # Combined score
    total_score = (impact_score * 0.5) + (confidence_score * 0.3) + (payback_score * 0.2)
    
    if total_score >= 80:
        return "CRITICAL - Immediate action required"
    elif total_score >= 60:
        return "HIGH - Schedule within 30 days"
    elif total_score >= 40:
        return "MEDIUM - Plan for next quarter"
    else:
        return "LOW - Consider for annual planning"

def create_executive_summary(
    insights: List[Dict[str, Any]],
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """Create an executive summary from multiple insights.
    
    Args:
        insights: List of formatted insights
        tool_context: ADK tool context for state management
        
    Returns:
        Executive summary with total impact and prioritized actions
    """
    if not insights:
        return {"error": "No insights provided for summary"}
    
    # Calculate totals
    total_impact = sum(
        float(i["annual_impact"].replace("$", "").replace(",", ""))
        for i in insights
        if "annual_impact" in i
    )
    
    # Sort by priority
    priority_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    sorted_insights = sorted(
        insights,
        key=lambda x: (
            priority_order.index(x.get("priority", "LOW").split(" - ")[0]),
            -float(x.get("annual_impact", "$0").replace("$", "").replace(",", ""))
        )
    )
    
    # Create summary
    summary = {
        "executive_summary": {
            "total_opportunity": f"${total_impact:,.0f}",
            "insight_count": len(insights),
            "critical_actions": sum(1 for i in insights if "CRITICAL" in i.get("priority", "")),
            "average_payback": f"{sum(float(i.get('payback_period', '0 months').split()[0]) for i in insights) / len(insights):.1f} months"
        },
        "prioritized_insights": sorted_insights[:5],  # Top 5
        "quick_wins": [
            i for i in sorted_insights 
            if float(i.get("payback_period", "12 months").split()[0]) < 3
        ][:3],
        "generated_at": datetime.now().isoformat()
    }
    
    # Track in state
    if tool_context:
        summaries = tool_context.state.get("executive_summaries", [])
        summaries.append(summary)
        tool_context.state["executive_summaries"] = summaries
    
    return summary