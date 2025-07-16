import re
from typing import Dict, Any, List

def validate_and_optimize_query(query: str) -> str:
    """Validate and optimize SPARQL queries for Owlready2"""
    
    # Add DISTINCT to prevent duplicate results
    if "SELECT ?" in query and "DISTINCT" not in query:
        if not any(agg in query for agg in ["COUNT", "SUM", "AVG", "MIN", "MAX"]):
            query = query.replace("SELECT ?", "SELECT DISTINCT ?")
    
    # Add LIMIT for exploration queries
    if "ORDER BY" in query and "LIMIT" not in query:
        query = query.rstrip().rstrip("}") + "\nLIMIT 100\n}"
    
    # Check for missing GROUP BY with aggregations
    if any(f"({agg}" in query for agg in ["COUNT", "SUM", "AVG"]):
        if "GROUP BY" not in query:
            # Extract non-aggregated variables
            select_match = re.search(r"SELECT.*?WHERE", query, re.DOTALL)
            if select_match:
                vars_in_select = re.findall(r"\?(\w+)(?!\s*\))", select_match.group())
                if vars_in_select:
                    query = query.rstrip().rstrip("}") + f"\nGROUP BY ?{' ?'.join(vars_in_select)}\n}}"
    
    return query

def analyze_query_failure(query: str, error: str) -> Dict[str, Any]:
    """Analyze why a query failed and suggest fixes"""
    
    suggestions = []
    
    if "Undefined prefix" in error:
        suggestions.append("Use full prefix 'mes_ontology_populated:' for all properties")
    
    if "FILTER(ISIRI(?timestamp))" in query and "0 results" in error:
        suggestions.append("Remove FILTER(ISIRI(?timestamp)) - timestamps are literals")
        fixed_query = query.replace("FILTER(ISIRI(?timestamp))", "")
        return {"suggestions": suggestions, "fixed_query": fixed_query}
    
    if "syntax error" in error.lower():
        # Check for common syntax issues
        if query.count("{") != query.count("}"):
            suggestions.append("Mismatched braces - check opening and closing braces")
        
        if "SELECT" in query and "WHERE" not in query:
            suggestions.append("Missing WHERE clause")
            
        if re.search(r"[^?]\w+:", query) and "PREFIX" not in query:
            suggestions.append("Using prefixed names without PREFIX declaration")
    
    if "0 results" in error and "timestamp" in query.lower():
        suggestions.append("Check timestamp format - should be literals with xsd:dateTime type")
        suggestions.append("Example: \"2024-01-01T00:00:00\"^^xsd:dateTime")
    
    return {"suggestions": suggestions}

def extract_query_pattern(query: str) -> Dict[str, Any]:
    """Extract reusable patterns from successful queries"""
    
    pattern = {
        "uses_aggregation": any(agg in query for agg in ["COUNT", "SUM", "AVG", "MIN", "MAX"]),
        "uses_grouping": "GROUP BY" in query,
        "uses_ordering": "ORDER BY" in query,
        "uses_distinct": "DISTINCT" in query,
        "uses_filters": "FILTER" in query,
        "timestamp_handling": "xsd:dateTime" in query,
        "namespace_prefix": "mes_ontology_populated:" in query
    }
    
    # Extract WHERE clause patterns
    where_match = re.search(r"WHERE\s*{(.*?)}", query, re.DOTALL)
    if where_match:
        where_content = where_match.group(1)
        pattern["triple_patterns"] = len(re.findall(r"\.", where_content))
        pattern["filter_count"] = len(re.findall(r"FILTER", where_content))
    
    return pattern

def suggest_query_improvements(query: str, results: Dict[str, Any]) -> List[str]:
    """Suggest improvements based on query results"""
    
    suggestions = []
    
    if results.get("row_count", 0) > 1000:
        suggestions.append("Consider adding LIMIT clause to reduce result size")
        suggestions.append("Add aggregation functions to summarize data")
    
    if results.get("row_count", 0) == 0:
        suggestions.append("No results - try removing some FILTER conditions")
        suggestions.append("Check if property names are correct with discover_properties tool")
    
    # Check for duplicate results
    if results.get("results"):
        first_10 = results["results"][:10]
        if len(first_10) > 1 and all(row == first_10[0] for row in first_10[1:]):
            suggestions.append("Duplicate results detected - add DISTINCT or use aggregation")
            suggestions.append("Consider GROUP BY to aggregate duplicate rows")
    
    return suggestions