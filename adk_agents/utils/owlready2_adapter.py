"""
Adapter for converting standard SPARQL to Owlready2-compatible format.
Based on patterns from owlready2_sparql_master_reference.md
"""
import re
from typing import Dict, List, Optional


class Owlready2Adapter:
    """Adapts standard SPARQL queries for Owlready2 compatibility."""
    
    def __init__(self, namespace: str = "http://example.com/mes#"):
        self.namespace = namespace
        self.auto_prefix = f"PREFIX : <{namespace}>"
    
    def adapt_query(self, query: str) -> str:
        """
        Adapt a standard SPARQL query for Owlready2 compatibility.
        
        Key adaptations:
        1. Remove PREFIX declarations
        2. Remove angle brackets
        3. Add automatic prefix
        4. Convert property syntax
        5. Add FILTER(ISIRI()) where needed
        """
        # Store original for debugging
        original_query = query
        
        # Remove all PREFIX declarations
        query = re.sub(r'PREFIX\s+\w+:\s*<[^>]+>\s*', '', query, flags=re.IGNORECASE)
        
        # Remove angle brackets from URIs
        query = re.sub(r'<([^>]+)>', r'\1', query)
        
        # Convert standard property paths to Owlready2 format
        # mes:hasEquipmentID -> :hasEquipmentID
        query = re.sub(r'\bmes:(\w+)', r':\1', query)
        
        # Convert rdf:type to 'a'
        query = re.sub(r'\brdf:type\b', 'a', query)
        
        # Add automatic prefix
        query = f"{self.auto_prefix}\n{query.strip()}"
        
        # Add FILTER(ISIRI()) for entity variables if not present
        query = self._add_iri_filters(query)
        
        return query
    
    def _add_iri_filters(self, query: str) -> str:
        """Add FILTER(ISIRI()) for entity variables where appropriate."""
        # This is a simplified implementation - in production, 
        # we'd parse the query properly
        
        # Find SELECT variables that look like entities
        select_match = re.search(r'SELECT\s+(.*?)\s+WHERE', query, re.IGNORECASE | re.DOTALL)
        if select_match:
            variables = select_match.group(1).split()
            entity_vars = [v for v in variables if v.startswith('?') and 
                          not any(kw in v.lower() for kw in ['value', 'score', 'count', 'avg', 'sum'])]
            
            # Check if WHERE clause already has FILTER(ISIRI()) for these vars
            where_match = re.search(r'WHERE\s*\{(.*)\}', query, re.IGNORECASE | re.DOTALL)
            if where_match:
                where_clause = where_match.group(1)
                for var in entity_vars:
                    if f'FILTER(ISIRI({var}))' not in where_clause:
                        # Add filter at the end of WHERE clause
                        query = query.replace('}', f'\n    FILTER(ISIRI({var}))\n}}', 1)
        
        return query
    
    def format_results(self, results: Dict) -> List[Dict]:
        """
        Format Owlready2 SPARQL results to standard format.
        
        Handles the specific JSON structure returned by Owlready2.
        """
        if not results or 'data' not in results:
            return []
        
        data = results['data']
        if 'results' in data:
            return data['results']
        
        # Handle different response formats
        if isinstance(data, list):
            return data
        
        return []
    
    def build_equipment_query(self, oee_threshold: float = 85.0) -> str:
        """Build a query to find underperforming equipment."""
        query = f"""
        SELECT DISTINCT ?equipment ?equipmentID ?avgOEE
        WHERE {{
            ?event a :ProductionLog .
            ?event :logsEquipment ?equipment .
            ?equipment :hasEquipmentID ?equipmentID .
            ?event :hasOEEScore ?oee .
            
            FILTER(ISIRI(?equipment))
            FILTER(?oee < {oee_threshold})
        }}
        """
        return self.adapt_query(query)
    
    def build_temporal_query(self, time_window_hours: int = 24) -> str:
        """Build a query for temporal pattern analysis."""
        query = f"""
        SELECT ?timestamp ?equipment ?eventType ?duration
        WHERE {{
            {{
                ?event a :DowntimeLog .
                ?event :logsEquipment ?equipment .
                ?event :hasTimestamp ?timestamp .
                ?event :hasDowntimeDuration ?duration .
                BIND("downtime" AS ?eventType)
            }}
            UNION
            {{
                ?event a :ProductionLog .
                ?event :logsEquipment ?equipment .
                ?event :hasTimestamp ?timestamp .
                ?event :hasOEEScore ?oee .
                FILTER(?oee < 70.0)
                BIND("low_oee" AS ?eventType)
                BIND(0 AS ?duration)
            }}
            
            FILTER(ISIRI(?equipment))
        }}
        ORDER BY ?timestamp
        """
        return self.adapt_query(query)
    
    def build_financial_impact_query(self, equipment_id: str) -> str:
        """Build a query to calculate financial impact for specific equipment."""
        query = f"""
        SELECT ?product ?goodUnits ?scrapUnits ?targetRate ?unitCost ?salePrice
        WHERE {{
            ?event a :ProductionLog .
            ?event :logsEquipment ?equipment .
            ?equipment :hasEquipmentID "{equipment_id}" .
            ?event :producesProduct ?product .
            ?product :hasProductName ?productName .
            ?event :hasGoodUnitsProduced ?goodUnits .
            ?event :hasScrapUnitsProduced ?scrapUnits .
            ?product :hasTargetRate ?targetRate .
            ?product :hasStandardCost ?unitCost .
            ?product :hasSalePrice ?salePrice .
            
            FILTER(ISIRI(?equipment))
            FILTER(ISIRI(?product))
        }}
        """
        return self.adapt_query(query)


# Singleton instance
adapter = Owlready2Adapter()


def adapt_sparql_for_owlready2(query: str) -> str:
    """Convenience function to adapt SPARQL queries."""
    return adapter.adapt_query(query)


def format_owlready2_results(results: Dict) -> List[Dict]:
    """Convenience function to format results."""
    return adapter.format_results(results)