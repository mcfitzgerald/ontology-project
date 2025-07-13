"""
Utility functions for the SPARQL API
"""

import re
import time
import logging
from typing import Optional, Tuple, List, Any
from datetime import datetime
from functools import lru_cache
from owlready2 import World

from .models import QueryType


logger = logging.getLogger(__name__)


def detect_query_type(query: str) -> QueryType:
    """
    Detect the type of SPARQL query from the query string.
    
    Args:
        query: SPARQL query string
        
    Returns:
        QueryType enum value
    """
    # Normalize whitespace and convert to uppercase for checking
    query_upper = ' '.join(query.strip().split()).upper()
    
    if query_upper.startswith("SELECT"):
        return QueryType.SELECT
    elif query_upper.startswith("INSERT"):
        return QueryType.INSERT
    elif query_upper.startswith("DELETE"):
        return QueryType.DELETE
    else:
        return QueryType.UNKNOWN


def quick_sparql_check(query: str, max_length: int) -> Optional[str]:
    """
    Perform basic sanity checks on SPARQL query.
    Returns warning message if issues found, None if OK.
    
    Args:
        query: SPARQL query string
        max_length: Maximum allowed query length
        
    Returns:
        Warning message or None
    """
    # Check length
    if len(query) > max_length:
        return f"Query exceeds maximum length of {max_length} characters"
    
    # Check for balanced braces
    if query.count("{") != query.count("}"):
        return "Warning: Unbalanced braces detected"
    
    # Check for balanced parentheses
    if query.count("(") != query.count(")"):
        return "Warning: Unbalanced parentheses detected"
    
    # Check for unsupported operations based on Owlready2 documentation
    query_upper = query.upper()
    
    # Unsupported query types
    unsupported_types = ["ASK", "DESCRIBE", "CONSTRUCT", "LOAD", "CLEAR", "DROP"]
    for unsupported in unsupported_types:
        if re.search(rf'\b{unsupported}\b', query_upper):
            return f"Query type {unsupported} is not supported by Owlready2"
    
    # Unsupported clauses
    if "DELETE WHERE" in query_upper:
        return "DELETE WHERE is not supported, use DELETE with WHERE clause"
    
    if "INSERT DATA" in query_upper or "DELETE DATA" in query_upper:
        return "INSERT DATA / DELETE DATA not supported, use INSERT/DELETE with WHERE"
    
    if re.search(r'\bFROM\s+NAMED\b', query_upper) or re.search(r'\bFROM\b(?!\s*\()', query_upper):
        return "FROM / FROM NAMED clauses are not supported"
    
    if re.search(r'\bSERVICE\b', query_upper):
        return "SERVICE (federated queries) not supported"
    
    if re.search(r'\bMINUS\b', query_upper):
        return "MINUS operator is not supported"
    
    return None


def sanitize_query(query: str) -> str:
    """
    Lightly sanitize SPARQL query without changing semantics.
    
    Args:
        query: Original SPARQL query
        
    Returns:
        Sanitized query
    """
    # Remove single-line comments (but preserve strings)
    # This is a simple approach - more robust would parse properly
    lines = query.split('\n')
    sanitized_lines = []
    
    for line in lines:
        # Simple comment removal - doesn't handle # in strings perfectly
        comment_pos = line.find('#')
        if comment_pos >= 0:
            # Check if it's likely in a string (very basic check)
            before_comment = line[:comment_pos]
            if before_comment.count('"') % 2 == 0 and before_comment.count("'") % 2 == 0:
                line = line[:comment_pos]
        sanitized_lines.append(line)
    
    # Join and normalize whitespace
    sanitized = ' '.join(' '.join(sanitized_lines).split())
    
    return sanitized


@lru_cache(maxsize=128)
def get_error_hint(error_message: str) -> Optional[str]:
    """
    Provide helpful hints based on common Owlready2 error messages.
    
    Args:
        error_message: The error message from Owlready2
        
    Returns:
        Helpful hint or None
    """
    error_lower = error_message.lower()
    
    if "unknown prefix" in error_lower:
        return "Check prefix definitions. Owlready2 auto-defines common prefixes (rdf, rdfs, owl, xsd) and ontology prefixes."
    
    if "syntax error" in error_lower:
        return "Check SPARQL syntax. Common issues: missing dots, unbalanced brackets, incorrect property paths."
    
    if "unknown property" in error_lower:
        return "Ensure the property exists in the ontology. Use full IRI if prefix is not defined."
    
    if "type error" in error_lower or "cannot convert" in error_lower:
        return "Check data types in query. Ensure literals match expected types (string, int, float, datetime)."
    
    if "not supported" in error_lower:
        return "This SPARQL feature may not be supported by Owlready2. Check documentation for supported features."
    
    return None


# Common RDF/OWL predicate mappings for Owlready2 internal IDs
PREDICATE_IRI_MAPPING = {
    6: "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
    7: "http://www.w3.org/2000/01/rdf-schema#domain",
    8: "http://www.w3.org/2000/01/rdf-schema#range",
    9: "http://www.w3.org/2000/01/rdf-schema#subClassOf",
    10: "http://www.w3.org/2002/07/owl#equivalentClass",
    11: "http://www.w3.org/2002/07/owl#NamedIndividual",
    12: "http://www.w3.org/2000/01/rdf-schema#subPropertyOf",
    13: "http://www.w3.org/2002/07/owl#ObjectProperty",
    14: "http://www.w3.org/2002/07/owl#DatatypeProperty",
    15: "http://www.w3.org/2002/07/owl#AnnotationProperty",
    16: "http://www.w3.org/2002/07/owl#inverseOf",
    17: "http://www.w3.org/2002/07/owl#TransitiveProperty",
    18: "http://www.w3.org/2002/07/owl#SymmetricProperty",
    19: "http://www.w3.org/2002/07/owl#AsymmetricProperty",
    20: "http://www.w3.org/2002/07/owl#ReflexiveProperty",
    21: "http://www.w3.org/2002/07/owl#IrreflexiveProperty",
    22: "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property",
}


def format_query_results(results: List[List[Any]], columns: List[str], world: Optional[World] = None, use_names: bool = True) -> Tuple[List[List[Any]], List[str]]:
    """
    Format query results for JSON serialization.
    
    Args:
        results: Raw query results from Owlready2
        columns: Column names from the query
        world: Owlready2 World object for resolving IRIs
        use_names: If True, use entity names instead of full IRIs (default: True)
        
    Returns:
        Tuple of (formatted_results, formatted_columns)
    """
    formatted_results = []
    
    for row in results:
        formatted_row = []
        for value in row:
            formatted_value = None
            
            # Handle integer predicates (Owlready2 internal IDs)
            if isinstance(value, int) and world is not None:
                # Try to unabbreviate the integer to get IRI
                try:
                    iri = world._unabbreviate(value)
                    formatted_value = iri
                except:
                    # Fall back to predicate mapping
                    if value in PREDICATE_IRI_MAPPING:
                        formatted_value = PREDICATE_IRI_MAPPING[value]
                    else:
                        # If all else fails, keep the integer
                        formatted_value = value
            
            # Handle type objects (Python classes)
            elif isinstance(value, type):
                # It's a Python type/class object
                if hasattr(value, 'name') and use_names:
                    # Use the entity name if available
                    formatted_value = value.name
                elif hasattr(value, 'iri'):
                    formatted_value = value.iri
                elif hasattr(value, '__module__') and hasattr(value, '__name__'):
                    # Create a string representation
                    formatted_value = f"{value.__module__}.{value.__name__}"
                else:
                    formatted_value = str(value)
            
            # Handle Owlready2 entities
            elif hasattr(value, 'iri'):
                if hasattr(value, 'name') and use_names:
                    # Use entity name for cleaner output
                    formatted_value = value.name
                else:
                    # Use full IRI
                    formatted_value = value.iri
            
            # Handle objects with name attribute
            elif hasattr(value, 'name') and not isinstance(value, (str, int, float, bool)):
                formatted_value = str(value.name)
            
            # Handle datetime objects
            elif isinstance(value, (datetime,)):
                formatted_value = value.isoformat()
            
            # Keep primitives as is
            else:
                formatted_value = value
            
            formatted_row.append(formatted_value)
        formatted_results.append(formatted_row)
    
    # Clean up column names (remove ? prefix if present)
    formatted_columns = [col.lstrip('?') for col in columns]
    
    return formatted_results, formatted_columns


class Timer:
    """Context manager for timing operations"""
    
    def __init__(self):
        self.start_time = None
        self.elapsed_ms = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        self.elapsed_ms = int((end_time - self.start_time) * 1000)


def truncate_results(results: List[List[Any]], max_rows: Optional[int]) -> Tuple[List[List[Any]], bool]:
    """
    Truncate results if they exceed max_rows limit.
    
    Args:
        results: Query results
        max_rows: Maximum number of rows to return
        
    Returns:
        Tuple of (truncated_results, was_truncated)
    """
    if max_rows is None or len(results) <= max_rows:
        return results, False
    
    return results[:max_rows], True