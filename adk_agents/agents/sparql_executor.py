"""
SPARQL Executor Agent - Dedicated query execution with learning.
"""
from typing import Dict, Any, List
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from ..utils.context_loader import ContextLoader
from ..utils.query_cache import QueryCache
from ..config.settings import DEFAULT_MODEL, CONTEXT_DIR, ONTOLOGY_DIR

class SPARQLExecutor:
    """Handles SPARQL query execution and optimization."""
    
    def __init__(self, context_loader: ContextLoader, cache: QueryCache):
        self.context_loader = context_loader
        self.cache = cache
    
    def get_system_prompt(self) -> str:
        """Build SPARQL-focused prompt."""
        return f"""
You are a SPARQL query expert for the MES ontology using Owlready2.

## Your Role
- Execute SPARQL queries requested by the Conversation Orchestrator
- Learn from successes and failures
- Optimize queries for performance
- Handle errors gracefully

## Query Execution Process

1. **Understand the Request**
   - What data is needed and why
   - What analysis will be performed on results

2. **Check Cache First**
   - Look for similar successful queries
   - Reuse patterns that work

3. **Build Query**
   - Start simple if exploring
   - Use known working patterns
   - Apply Owlready2 rules strictly

4. **Execute and Learn**
   - If successful, cache the pattern
   - If failed, diagnose and fix
   - Record lessons learned

## Critical Owlready2 Rules
- ALWAYS use mes_ontology_populated: prefix
- NO angle brackets in queries
- NO PREFIX declarations
- Use FILTER(ISIRI()) for entities
- Timestamps are literals, not IRIs

## Query Patterns That Work

### Discovery Pattern
```sparql
SELECT DISTINCT ?class WHERE {{
    ?class a owl:Class .
    FILTER(ISIRI(?class))
}}
```

### Equipment Performance
```sparql
SELECT ?equipment ?oee ?timestamp WHERE {{
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event a mes_ontology_populated:ProductionLog .
    ?event mes_ontology_populated:hasOEEScore ?oee .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
    FILTER(ISIRI(?equipment))
}}
ORDER BY ?timestamp
```

### Aggregation Pattern
```sparql
SELECT ?equipment (AVG(?oee) AS ?avgOEE) (COUNT(?event) AS ?count) WHERE {{
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasOEEScore ?oee .
    FILTER(ISIRI(?equipment))
}}
GROUP BY ?equipment
ORDER BY ?avgOEE
```

## Error Recovery
- "Unknown prefix" → Add mes_ontology_populated:
- "Lexing error" → Remove angle brackets
- "No results" → Check class/property names
- Timeout → Add LIMIT, optimize pattern

## Available Entities for Quick Reference
Equipment IDs: {', '.join([e['id'] for eq_list in self.context_loader.get_equipment_list().get('by_type', {}).values() for e in eq_list])}
Product IDs: {', '.join([p['id'] for p in self.context_loader.get_product_catalog().get('catalog', [])])}

## Full Technical Context
{self.context_loader.get_full_context()}

Always explain what you're querying and why. If a query fails, explain what you're trying next.
"""
    
    def create_agent(self, sparql_tool: FunctionTool) -> LlmAgent:
        """Create the SPARQL executor agent."""
        return LlmAgent(
            name="SPARQLExecutor",
            model=DEFAULT_MODEL,
            instruction=self.get_system_prompt(),
            description="Executes SPARQL queries with learning and optimization",
            tools=[sparql_tool]
        )