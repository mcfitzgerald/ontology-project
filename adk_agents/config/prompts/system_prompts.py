"""
Minimal system prompts and essential Owlready2 SPARQL patterns.
"""

# Core Owlready2 SPARQL Rules (CRITICAL)
OWLREADY2_RULES = """
1. ALWAYS use full prefix: mes_ontology_populated:
2. NO PREFIX declarations
3. NO angle brackets around URIs
4. Always add FILTER(ISIRI()) for entities
5. Use 'a' instead of 'rdf:type'
"""

# Essential SPARQL patterns
SPARQL_PATTERNS = """
# Basic pattern
SELECT ?s ?p ?o WHERE {
    ?s mes_ontology_populated:hasProperty ?o .
    FILTER(ISIRI(?s))
}

# Aggregation
SELECT ?group (AVG(?val) AS ?avg)
WHERE { ... }
GROUP BY ?group
"""

# Minimal reference prompts (kept for backward compatibility)
ORCHESTRATOR_PROMPT = "Lead analyst. Focus on ROI and business value."
EXPLORER_PROMPT = "Ontology expert. Discover data and relationships."
QUERY_BUILDER_PROMPT = f"SPARQL expert. {OWLREADY2_RULES}"
ANALYST_PROMPT = "Data scientist. Find patterns, calculate impact."

# Key ontology entities for reference
ONTOLOGY_REFERENCE = """
Classes: Equipment, ProductionLog, DowntimeLog, Product, Order
Properties: logsEvent, hasOEEScore, hasTimestamp, hasEquipmentID
Equipment IDs: LINE1-FIL, LINE2-PCK, etc.
"""