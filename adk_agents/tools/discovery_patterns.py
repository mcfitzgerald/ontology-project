"""Discovery patterns tool providing proven analysis approaches."""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

def get_discovery_pattern(
    pattern_type: str, 
    context: Optional[str] = None,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """Get a proven discovery pattern with approach and starter queries.
    
    Args:
        pattern_type: Type of pattern - hidden_capacity, temporal_anomaly, quality_tradeoff, etc.
        context: Additional context about the specific scenario
        tool_context: ADK tool context for accessing state
        
    Returns:
        Pattern details including description, approach, queries, and value calculation
    """
    patterns = {
        "hidden_capacity": {
            "description": "Find gap between current and benchmark performance",
            "approach": [
                "1. Query current OEE/performance metrics by equipment",
                "2. Compare to world-class benchmark (85% OEE)",
                "3. Calculate production volume during performance gaps",
                "4. Multiply lost volume by product margins"
            ],
            "starter_queries": [
                """SELECT ?equipment ?line ?oee ?timestamp WHERE {
    ?equipment mes_ontology_populated:belongsToLine ?line .
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasOEEScore ?oee .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
    FILTER(?oee < 85.0)
    FILTER(ISIRI(?equipment))
} ORDER BY ?oee LIMIT 200""",
                """SELECT ?equipment ?line (AVG(?oee) AS ?avgOEE) WHERE {
    ?equipment mes_ontology_populated:belongsToLine ?line .
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event a mes_ontology_populated:ProductionLog .
    ?event mes_ontology_populated:hasOEEScore ?oee .
    FILTER(?oee > 0.0)
    FILTER(ISIRI(?equipment))
} GROUP BY ?equipment ?line ORDER BY ?avgOEE"""
            ],
            "value_formula": "(benchmark_oee - current_oee) × annual_volume × unit_margin",
            "typical_findings": "10-20% hidden capacity worth $500K-2M annually"
        },
        
        "temporal_anomaly": {
            "description": "Identify time-based patterns in failures or performance",
            "approach": [
                "1. Query events/failures by timestamp",
                "2. Extract hour, shift, or day patterns",
                "3. Look for clustering or periodicity",
                "4. Calculate cost of preventing predictable issues"
            ],
            "starter_queries": [
                """SELECT ?equipment ?timestamp ?reason WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event a mes_ontology_populated:DowntimeLog .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
    ?event mes_ontology_populated:hasDowntimeReason ?reason .
    FILTER(ISIRI(?equipment))
} ORDER BY ?timestamp LIMIT 500""",
                """SELECT ?line (SUBSTR(?timestamp, 12, 2) AS ?hour) WHERE {
    ?equipment mes_ontology_populated:belongsToLine ?line .
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event a mes_ontology_populated:DowntimeLog .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
    FILTER(ISIRI(?line))
} LIMIT 1000"""
            ],
            "value_formula": "prevented_incidents × avg_downtime_minutes × cost_per_minute",
            "typical_findings": "40% of issues cluster in specific hours/shifts"
        },
        
        "quality_tradeoff": {
            "description": "Balance quality improvements against their costs",
            "approach": [
                "1. Query quality scores and scrap rates by product",
                "2. Calculate current scrap costs",
                "3. Estimate improvement costs (inspection, equipment)",
                "4. Find optimal quality target for ROI"
            ],
            "starter_queries": [
                """SELECT ?product (AVG(?qualityScore) AS ?avgQuality) WHERE {
    ?equipment mes_ontology_populated:executesOrder ?order .
    ?order mes_ontology_populated:producesProduct ?product .
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event a mes_ontology_populated:ProductionLog .
    ?event mes_ontology_populated:hasQualityScore ?qualityScore .
    FILTER(?qualityScore < 98.0)
    FILTER(ISIRI(?product))
} GROUP BY ?product ORDER BY ?avgQuality""",
                """SELECT DISTINCT ?product ?productName ?salePrice ?standardCost WHERE {
    ?product a mes_ontology_populated:Product .
    ?product mes_ontology_populated:hasProductName ?productName .
    ?product mes_ontology_populated:hasSalePrice ?salePrice .
    ?product mes_ontology_populated:hasStandardCost ?standardCost .
} ORDER BY ?product"""
            ],
            "value_formula": "(current_scrap_rate - target_scrap_rate) × annual_volume × unit_cost",
            "typical_findings": "1% quality improvement = $100K-500K annually"
        },
        
        "product_impact": {
            "description": "Identify which products hurt or help performance",
            "approach": [
                "1. Query OEE/performance metrics by product",
                "2. Compare product-specific performance",
                "3. Identify 'problem products' vs 'easy runners'",
                "4. Calculate impact of optimizing product mix"
            ],
            "starter_queries": [
                """SELECT ?product (AVG(?oee) AS ?avgOEE) WHERE {
    ?equipment mes_ontology_populated:executesOrder ?order .
    ?order mes_ontology_populated:producesProduct ?product .
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasOEEScore ?oee .
    ?event a mes_ontology_populated:ProductionLog .
    FILTER(?oee > 0.0)
    FILTER(ISIRI(?product))
} GROUP BY ?product ORDER BY ?avgOEE""",
                """SELECT ?equipment ?product ?performance WHERE {
    ?equipment mes_ontology_populated:executesOrder ?order .
    ?order mes_ontology_populated:producesProduct ?product .
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasPerformanceScore ?performance .
    FILTER(?performance < 85.0)
    FILTER(ISIRI(?equipment))
} LIMIT 100"""
            ],
            "value_formula": "(good_product_oee - bad_product_oee) × volume × margin",
            "typical_findings": "Certain SKUs consistently underperform by 10-20%"
        },
        
        "root_cause": {
            "description": "Find why problems occur repeatedly",
            "approach": [
                "1. Query failure reasons and their frequency",
                "2. Trace patterns in equipment, time, products",
                "3. Identify systemic vs random issues",
                "4. Calculate ROI of addressing root causes"
            ],
            "starter_queries": [
                """SELECT ?reason WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event a mes_ontology_populated:DowntimeLog .
    ?event mes_ontology_populated:hasDowntimeReason ?reason .
    FILTER(ISIRI(?reason))
} LIMIT 200""",
                """SELECT ?equipment ?line (MIN(?timestamp) AS ?first) (MAX(?timestamp) AS ?last) WHERE {
    ?equipment mes_ontology_populated:belongsToLine ?line .
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event a mes_ontology_populated:DowntimeLog .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
    FILTER(ISIRI(?equipment) && ISIRI(?line))
} GROUP BY ?equipment ?line ORDER BY ?line"""
            ],
            "value_formula": "incidents_prevented × avg_cost_per_incident",
            "typical_findings": "80% of downtime from 20% of causes"
        }
    }
    
    # Track pattern usage in state
    if tool_context and pattern_type in patterns:
        patterns_used = tool_context.state.get("patterns_used", [])
        patterns_used.append({
            "pattern": pattern_type,
            "context": context,
            "timestamp": datetime.now().isoformat()
        })
        tool_context.state["patterns_used"] = patterns_used
    
    # Return the requested pattern or a helpful error
    if pattern_type in patterns:
        result = patterns[pattern_type].copy()
        if context:
            result["applied_context"] = context
        return result
    else:
        return {
            "error": f"Unknown pattern type: {pattern_type}",
            "available_patterns": list(patterns.keys()),
            "suggestion": "Try one of the available patterns or describe what you're looking for"
        }

def list_discovery_patterns(tool_context: Optional[ToolContext] = None) -> Dict[str, Any]:
    """List all available discovery patterns with brief descriptions.
    
    Args:
        tool_context: ADK tool context for accessing state
        
    Returns:
        Dictionary of pattern names and descriptions
    """
    patterns = {
        "hidden_capacity": "Find gap between current and benchmark performance",
        "temporal_anomaly": "Identify time-based patterns in failures",
        "quality_tradeoff": "Balance quality improvements against costs",
        "product_impact": "Identify which products hurt/help performance",
        "root_cause": "Find why problems occur repeatedly"
    }
    
    # Include patterns already used from state
    if tool_context:
        patterns_used = tool_context.state.get("patterns_used", [])
        used_names = [p["pattern"] for p in patterns_used]
        
        return {
            "available_patterns": patterns,
            "patterns_used": used_names,
            "suggestion": "Start with 'hidden_capacity' for quick wins"
        }
    
    return {
        "available_patterns": patterns,
        "suggestion": "Start with 'hidden_capacity' for quick wins"
    }