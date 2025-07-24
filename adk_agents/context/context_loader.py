"""Context loader for Manufacturing Analyst Agent."""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from ..config.settings import PROJECT_ROOT

logger = logging.getLogger(__name__)

class ContextLoader:
    """Loads and formats context for the Manufacturing Analyst Agent."""
    
    def __init__(self):
        self.context_dir = PROJECT_ROOT.parent / "Context"
        self.mindmap_path = self.context_dir / "mes_ontology_mindmap.ttl"
        self.sparql_ref_path = self.context_dir / "owlready2_sparql_lean_reference.md"
        self.data_catalogue_path = self.context_dir / "mes_data_catalogue.json"
        self.cache_dir = PROJECT_ROOT / "cache"
        
    def load_ontology_context(self) -> str:
        """Load complete ontology mindmap for context."""
        try:
            if self.mindmap_path.exists():
                with open(self.mindmap_path, 'r', encoding='utf-8') as f:
                    content = f.read()  # Read entire file
                return f"### Ontology Structure:\n{content}\n"
            else:
                logger.warning(f"Ontology mindmap not found at {self.mindmap_path}")
                return "### Ontology Structure: Not found\n"
        except Exception as e:
            logger.error(f"Failed to load ontology mindmap: {e}")
            return f"### Ontology Structure: Error loading - {e}\n"
    
    def load_sparql_reference(self) -> str:
        """Load SPARQL reference guide for Owlready2."""
        try:
            if self.sparql_ref_path.exists():
                with open(self.sparql_ref_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return f"### SPARQL Reference:\n{content}\n"
            else:
                # Provide essential rules if reference not found
                return """### SPARQL Reference:
CRITICAL RULES for Owlready2 SPARQL:
1. NEVER use PREFIX declarations
2. NEVER use angle brackets around URIs
3. Always use ontology name prefix: mes_ontology_populated:
4. Equipment is abstract - query concrete types: Filler, Packer, Palletizer
5. Always use FILTER(ISIRI(?var)) for entity variables
6. No regex() or str() functions supported
7. Use UNION for multiple equipment types
"""
        except Exception as e:
            logger.error(f"Failed to load SPARQL reference: {e}")
            return f"### SPARQL Reference: Error loading - {e}\n"
    
    def load_successful_queries(self) -> str:
        """Load examples of successful queries."""
        examples = []
        
        # Load from query cache if available
        cache_path = self.context_dir / "query_cache.json"
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)
                    for item in cache_data[:5]:  # First 5 examples
                        examples.append({
                            "purpose": item.get("purpose", "Unknown"),
                            "query": item.get("query", "")
                        })
            except Exception as e:
                logger.warning(f"Failed to load query cache: {e}")
        
        # Add essential query patterns
        if not examples:
            examples = [
                {
                    "purpose": "Get all equipment",
                    "query": """SELECT ?equipment WHERE {
    { ?equipment a mes_ontology_populated:Filler } UNION
    { ?equipment a mes_ontology_populated:Packer } UNION
    { ?equipment a mes_ontology_populated:Palletizer }
    FILTER(ISIRI(?equipment))
}"""
                },
                {
                    "purpose": "Get OEE scores with timestamps",
                    "query": """SELECT ?equipment ?oee ?timestamp WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasOEEScore ?oee .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
    FILTER(ISIRI(?equipment))
    FILTER(ISIRI(?event))
}"""
                },
                {
                    "purpose": "Production summary by product",
                    "query": """SELECT ?product (SUM(?good) as ?total_good) (SUM(?scrap) as ?total_scrap) WHERE {
    ?order mes_ontology_populated:producesProduct ?product .
    ?equipment mes_ontology_populated:executesOrder ?order .
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasGoodUnits ?good .
    ?event mes_ontology_populated:hasScrapUnits ?scrap .
    FILTER(ISIRI(?product))
    FILTER(ISIRI(?order))
    FILTER(ISIRI(?equipment))
    FILTER(ISIRI(?event))
} GROUP BY ?product"""
                },
                {
                    "purpose": "Get downtime events with reasons (avoid COUNT with GROUP BY)",
                    "query": """SELECT ?equipment ?reason WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event a mes_ontology_populated:DowntimeLog .
    ?event mes_ontology_populated:hasDowntimeReasonCode ?reason .
    FILTER(ISIRI(?equipment))
    FILTER(ISIRI(?event))
}"""
                },
                {
                    "purpose": "Average OEE by equipment (aggregation without COUNT)",
                    "query": """SELECT ?equipment (AVG(?oee) AS ?avg_oee) WHERE {
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasOEEScore ?oee .
    FILTER(ISIRI(?equipment))
}
GROUP BY ?equipment
ORDER BY ?avg_oee"""
                }
            ]
        
        # Format examples
        query_text = "### Successful Query Examples:\n"
        for i, example in enumerate(examples, 1):
            query_text += f"\n{i}. {example['purpose']}:\n```sparql\n{example['query']}\n```\n"
        
        return query_text
    
    def load_data_catalogue(self) -> str:
        """Load MES data catalogue information."""
        try:
            if self.data_catalogue_path.exists():
                with open(self.data_catalogue_path, 'r') as f:
                    catalogue = json.load(f)
                
                info = "### Data Catalogue:\n"
                
                # Metadata summary
                if "metadata" in catalogue:
                    meta = catalogue["metadata"]
                    info += f"- Data range: {meta['data_range']['start']} to {meta['data_range']['end']} ({meta['data_range']['days_covered']} days)\n"
                    info += f"- Total records: {meta['total_records']:,}\n"
                    info += f"- Update frequency: {meta['update_frequency']}\n\n"
                
                # Equipment summary
                if "equipment" in catalogue:
                    equipment = catalogue["equipment"]
                    info += f"- Equipment: {equipment['count']} units\n"
                    # Group by type
                    for eq_type, items in equipment.get("by_type", {}).items():
                        ids = [item["id"] for item in items]
                        info += f"  - {eq_type}: {', '.join(ids)}\n"
                    info += "\n"
                
                # Products summary
                if "products" in catalogue:
                    products = catalogue["products"]
                    info += f"- Products: {products['count']} SKUs\n"
                    for prod in products.get("catalog", [])[:5]:  # First 5 products
                        info += f"  - {prod['id']}: {prod['name']} (margin: {prod['margin_percent']}%)\n"
                    info += "\n"
                
                # Metrics summary
                if "metrics" in catalogue:
                    info += "- Key Metrics:\n"
                    for metric, values in catalogue["metrics"].items():
                        info += f"  - {metric}: mean={values['mean']}, typical={values['typical_range']}, benchmark={values['world_class']}\n"
                    info += "\n"
                
                # Downtime summary
                if "downtime_reasons" in catalogue:
                    downtime = catalogue["downtime_reasons"]
                    info += f"- Total downtime: {downtime['total_downtime_hours']} hours\n"
                    if downtime.get("unplanned"):
                        info += "  - Top unplanned reasons:\n"
                        for reason in downtime["unplanned"][:3]:
                            info += f"    - {reason['code']}: {reason['total_hours']} hours\n"
                
                return info
            else:
                return "### Data Catalogue: Not found\n"
        except Exception as e:
            logger.error(f"Failed to load data catalogue: {e}")
            return f"### Data Catalogue: Error loading - {e}\n"
    
    def get_comprehensive_context(self) -> str:
        """Get complete context for the Manufacturing Analyst Agent."""
        context_parts = [
            "## Manufacturing Analytics Context\n",
            "You are a Manufacturing Analyst specialized in analyzing MES (Manufacturing Execution System) data using SPARQL queries.\n",
            "\n### Key Capabilities:",
            "1. Convert business questions to SPARQL queries",
            "2. Analyze OEE (Overall Equipment Effectiveness) and production metrics",
            "3. Identify patterns and optimization opportunities",
            "4. Calculate financial impact and ROI\n",
            "\n### Domain Knowledge:",
            "- OEE = Availability � Performance � Quality",
            "- Standard OEE benchmark: 85%",
            "- Equipment types: Filler, Packer, Palletizer",
            "- Key metrics: OEE, production volume, quality rate, downtime\n",
            "\n" + self.load_sparql_reference(),
            "\n" + self.load_successful_queries(),
            "\n" + self.load_data_catalogue(),
            "\n### Query Construction Guidelines:",
            "1. Always use mes_ontology_populated: prefix",
            "2. Equipment must be queried by concrete types (Filler, Packer, Palletizer)",
            "3. Use FILTER(ISIRI(?var)) for all entity variables",
            "4. Use UNION to query multiple equipment types",
            "5. Timestamps are in ISO format",
            "6. For aggregations, use GROUP BY with appropriate aggregate functions\n",
            "\n### Analysis Approach:",
            "1. First understand what data is being requested",
            "2. Construct appropriate SPARQL query following the rules",
            "3. Execute query and check results",
            "4. Analyze patterns in the data",
            "5. Calculate financial impact where relevant",
            "6. Provide actionable insights\n"
        ]
        
        # Add ontology structure
        context_parts.append("\n" + self.load_ontology_context())
        
        return "\n".join(context_parts)
    
    def get_minimal_context(self) -> str:
        """Get minimal context for testing/debugging."""
        return """You are a Manufacturing Analyst Agent. Convert business questions to SPARQL queries for MES data.

Key rules:
- Use mes_ontology_populated: prefix
- Query equipment by concrete types: Filler, Packer, Palletizer
- Use FILTER(ISIRI(?var)) for entities
- No PREFIX declarations or angle brackets

Example query for OEE:
SELECT ?equipment ?oee WHERE {
    { ?equipment a mes_ontology_populated:Filler } UNION
    { ?equipment a mes_ontology_populated:Packer } UNION
    { ?equipment a mes_ontology_populated:Palletizer }
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasOEEScore ?oee .
    FILTER(ISIRI(?equipment))
    FILTER(ISIRI(?event))
}"""
    
    def get_essential_sparql_rules(self) -> str:
        """Get just the essential SPARQL rules."""
        return self.load_sparql_reference()
    
    def get_discovery_context(self) -> str:
        """Get focused context for discovery methodology."""
        return """## Discovery Methodology

CRITICAL RULE: **ALWAYS perform entity discovery BEFORE complex queries**
- When asked about equipment, FIRST discover what equipment exists
- When asked about lines, FIRST discover what lines exist
- Only AFTER discovering entities should you analyze their properties

Follow this approach to uncover valuable insights:

1. **EXPLORE** - Start simple to understand the data landscape
   - MANDATORY: First discover entities (equipment, lines) before analyzing them
   - Begin with basic queries to see what data exists
   - Check a few examples before diving deep
   - Build mental model of relationships

2. **DISCOVER** - When you find anomalies or patterns, dig deeper
   - If you see unexpected values, investigate why
   - Look for clustering, gaps, or outliers
   - Compare actual performance to benchmarks (e.g., 85% OEE)

3. **QUANTIFY** - Always translate findings to business impact
   - Convert operational metrics to financial value
   - Calculate annual impact (hourly × 24 × 365)
   - Use actual product margins and volumes

4. **RECOMMEND** - Provide specific actions with ROI
   - Suggest concrete next steps
   - Include implementation approach
   - Estimate payback period

## Key Behaviors

- **Start with curiosity**: What patterns might exist in this data?
- **Build incrementally**: Don't try complex queries first
- **Learn from failures**: If COUNT returns IRIs, immediately use the fallback query
- **Track discoveries**: Each finding guides the next question
- **Think like a detective**: Follow clues, test hypotheses
- **Always ask "So what?"**: Every finding must connect to value

## Analysis Patterns

When exploring data, consider these proven patterns:
- **Hidden Capacity**: Gap between current and benchmark performance
- **Temporal Patterns**: Time-based clustering of events
- **Product Impact**: Which products affect performance most
- **Quality Trade-offs**: Balance between quality and cost
- **Root Causes**: Why do problems occur repeatedly"""
    
    def get_python_analysis_context(self) -> str:
        """Get context for Python analysis capabilities."""
        return """## Advanced Analysis with Python

When SPARQL queries return large datasets (indicated by cache_id), use execute_python_code for sophisticated analysis:

1. **Start Simple**: First explore the data structure
   - Load data into DataFrame and check shape, columns, and preview
   - Always start with basic exploration before complex analysis

2. **Build Understanding**: Based on what you learn, dig deeper
   - Use describe() for statistical summaries
   - Check data types and missing values
   - Look for patterns in the distribution

3. **Discover Patterns**: Apply increasingly sophisticated analysis
   - Group by dimensions to find clusters
   - Look for temporal patterns and anomalies
   - Calculate correlations between metrics

4. **Quantify Impact**: Always connect findings to business value
   - Convert operational metrics to financial impact
   - Calculate annual projections
   - Estimate ROI of improvements

Remember: If code fails, learn from the error and try a different approach. Build your analysis iteratively."""

# Create singleton instance
context_loader = ContextLoader()