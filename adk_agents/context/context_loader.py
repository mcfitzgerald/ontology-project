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
        self.ontology_path = PROJECT_ROOT.parent / "Ontology" / "mes_ontology_populated.owl"
        self.context_dir = PROJECT_ROOT.parent / "Context"
        self.cache_dir = PROJECT_ROOT / "cache"
        
    def load_ontology_context(self, char_limit: int = 5000) -> str:
        """Load first N characters of ontology for context."""
        try:
            if self.ontology_path.exists():
                with open(self.ontology_path, 'r', encoding='utf-8') as f:
                    content = f.read(char_limit)
                return f"### Ontology (first {char_limit} chars):\n{content}\n"
            else:
                logger.warning(f"Ontology file not found at {self.ontology_path}")
                return "### Ontology: Not found\n"
        except Exception as e:
            logger.error(f"Failed to load ontology: {e}")
            return f"### Ontology: Error loading - {e}\n"
    
    def load_sparql_reference(self) -> str:
        """Load SPARQL reference guide for Owlready2."""
        ref_path = self.context_dir / "owlready2_sparql_lean_reference.md"
        try:
            if ref_path.exists():
                with open(ref_path, 'r', encoding='utf-8') as f:
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
                }
            ]
        
        # Format examples
        query_text = "### Successful Query Examples:\n"
        for i, example in enumerate(examples, 1):
            query_text += f"\n{i}. {example['purpose']}:\n```sparql\n{example['query']}\n```\n"
        
        return query_text
    
    def load_data_catalogue(self) -> str:
        """Load MES data catalogue information."""
        catalogue_path = self.context_dir / "mes_data_catalogue.json"
        try:
            if catalogue_path.exists():
                with open(catalogue_path, 'r') as f:
                    catalogue = json.load(f)
                
                info = "### Data Catalogue:\n"
                
                # Equipment summary
                if "equipment_catalog" in catalogue:
                    equipment = catalogue["equipment_catalog"]
                    info += f"- Equipment: {len(equipment)} items\n"
                    # Group by type
                    by_type = {}
                    for eq in equipment:
                        eq_type = eq.get("type", "Unknown")
                        if eq_type not in by_type:
                            by_type[eq_type] = []
                        by_type[eq_type].append(eq.get("id", ""))
                    
                    for eq_type, ids in by_type.items():
                        info += f"  - {eq_type}: {', '.join(ids)}\n"
                
                # Schema summary
                if "data_schema" in catalogue:
                    schema = catalogue["data_schema"]
                    info += f"\n- Data Schema: {len(schema)} columns\n"
                    # Key columns
                    key_cols = ["timestamp", "equipment_id", "oee_score", "good_units", "scrap_units"]
                    for col_info in schema:
                        if col_info.get("column") in key_cols:
                            info += f"  - {col_info['column']}: {col_info.get('description', '')}\n"
                
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
            "- OEE = Availability × Performance × Quality",
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
        
        # Add ontology snippet at the end
        context_parts.append("\n" + self.load_ontology_context(3000))
        
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

# Create singleton instance
context_loader = ContextLoader()