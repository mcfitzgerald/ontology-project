from typing import Dict, List, Optional
import re

class SPARQLQueryBuilder:
    """Enhanced SPARQL query builder with Owlready2 compatibility"""
    
    def __init__(self, namespace: str = "mes_ontology_populated"):
        self.namespace = namespace
        
    def build_downtime_pareto_query(self) -> str:
        """Build optimized Pareto analysis query with proper aggregation"""
        return f"""
        SELECT ?downtimeReason (COUNT(DISTINCT ?downtimeLog) AS ?count)
        WHERE {{
            ?downtimeLog a {self.namespace}:DowntimeLog .
            ?downtimeLog {self.namespace}:hasDowntimeReason ?downtimeReason .
            FILTER(ISIRI(?downtimeReason))
        }}
        GROUP BY ?downtimeReason
        ORDER BY DESC(?count)
        LIMIT 20
        """
    
    def build_time_series_query(self, 
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> str:
        """Build time series query treating timestamps as literals"""
        query = f"""
        SELECT ?timestamp ?line ?downtimeReason ?equipment
        WHERE {{
            ?downtimeLog a {self.namespace}:DowntimeLog .
            ?downtimeLog {self.namespace}:hasTimestamp ?timestamp .
            ?downtimeLog {self.namespace}:hasDowntimeReason ?downtimeReason .
            ?equipment {self.namespace}:logsEvent ?downtimeLog .
            ?equipment {self.namespace}:belongsToLine ?line .
            FILTER(ISIRI(?downtimeReason))
            FILTER(ISIRI(?line))
            # Timestamps are literals, not IRIs
        """
        
        if start_date or end_date:
            query += "\n            FILTER("
            if start_date:
                query += f'?timestamp >= "{start_date}"^^xsd:dateTime'
            if start_date and end_date:
                query += " && "
            if end_date:
                query += f'?timestamp <= "{end_date}"^^xsd:dateTime'
            query += ")"
            
        query += """
        }
        ORDER BY ?timestamp
        LIMIT 1000
        """
        return query
    
    def build_oee_analysis_query(self, equipment_type: Optional[str] = None) -> str:
        """Build OEE analysis query with proper aggregation"""
        base_query = f"""
        SELECT ?equipment (AVG(?oeeScore) AS ?avgOEE) (MIN(?oeeScore) AS ?minOEE) (MAX(?oeeScore) AS ?maxOEE)
        WHERE {{
            ?equipment a {self.namespace}:Equipment .
            ?oeeLog a {self.namespace}:OEELog .
            ?equipment {self.namespace}:logsEvent ?oeeLog .
            ?oeeLog {self.namespace}:hasOEEScore ?oeeScore .
        """
        
        if equipment_type:
            base_query += f"""
            ?equipment a {self.namespace}:{equipment_type} .
            """
            
        base_query += """
        }
        GROUP BY ?equipment
        ORDER BY ?avgOEE
        """
        return base_query
    
    def build_defect_analysis_query(self) -> str:
        """Build defect rate analysis query"""
        return f"""
        SELECT ?product ?line (COUNT(?defectLog) AS ?defectCount) (AVG(?defectRate) AS ?avgDefectRate)
        WHERE {{
            ?defectLog a {self.namespace}:QualityDefectLog .
            ?defectLog {self.namespace}:hasDefectRate ?defectRate .
            ?defectLog {self.namespace}:producedProduct ?product .
            ?equipment {self.namespace}:logsEvent ?defectLog .
            ?equipment {self.namespace}:belongsToLine ?line .
            FILTER(ISIRI(?product))
            FILTER(ISIRI(?line))
        }}
        GROUP BY ?product ?line
        ORDER BY DESC(?avgDefectRate)
        LIMIT 50
        """
    
    def build_equipment_properties_query(self, equipment_class: str) -> str:
        """Build query to discover properties of equipment"""
        return f"""
        SELECT DISTINCT ?property ?value
        WHERE {{
            ?equipment a {self.namespace}:{equipment_class} .
            ?equipment ?property ?value .
            FILTER(STRSTARTS(STR(?property), STR({self.namespace}:)))
        }}
        LIMIT 100
        """
    
    def build_progressive_query(self, base_pattern: str, 
                               filters: Optional[List[str]] = None,
                               aggregations: Optional[Dict[str, str]] = None,
                               group_by: Optional[List[str]] = None) -> str:
        """Build queries progressively with optional components"""
        
        # Start with SELECT clause
        select_vars = []
        if aggregations:
            for var, agg_func in aggregations.items():
                select_vars.append(f"({agg_func}({var}) AS {var}_agg)")
        
        # Extract variables from base pattern if no aggregations
        if not select_vars:
            var_pattern = re.compile(r'\?(\w+)')
            vars_in_pattern = list(set(var_pattern.findall(base_pattern)))
            select_vars = [f"?{var}" for var in vars_in_pattern]
        
        query = f"SELECT DISTINCT {' '.join(select_vars)}\nWHERE {{\n{base_pattern}"
        
        # Add filters
        if filters:
            for filter_clause in filters:
                query += f"\n    FILTER({filter_clause})"
        
        query += "\n}"
        
        # Add GROUP BY if needed
        if group_by:
            query += f"\nGROUP BY {' '.join(['?' + var for var in group_by])}"
        
        query += "\nLIMIT 100"
        
        return query