"""
Utility functions for the SPARQL API
"""

import re
import time
import logging
from typing import Optional, Tuple, List, Any
from datetime import datetime
from functools import lru_cache

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


def format_query_results(results: List[List[Any]], columns: List[str]) -> Tuple[List[List[Any]], List[str]]:
    """
    Format query results for JSON serialization.
    
    Args:
        results: Raw query results from Owlready2
        columns: Column names from the query
        
    Returns:
        Tuple of (formatted_results, formatted_columns)
    """
    formatted_results = []
    
    for row in results:
        formatted_row = []
        for value in row:
            # Convert Owlready2 objects to strings
            if hasattr(value, 'iri'):
                # It's an Owlready2 entity
                formatted_row.append(value.iri)
            elif hasattr(value, 'name'):
                # It might have a name attribute
                formatted_row.append(str(value.name))
            elif isinstance(value, (datetime,)):
                # Convert datetime to ISO format
                formatted_row.append(value.isoformat())
            else:
                # Keep as is (primitives, None, etc.)
                formatted_row.append(value)
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