"""SPARQL execution tool with caching and pattern learning."""
import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
from pathlib import Path
import logging
import re

from ..config.settings import (
    SPARQL_ENDPOINT, SPARQL_TIMEOUT, SPARQL_MAX_RESULTS,
    CACHE_DIR, CACHE_ENABLED, get_sparql_config
)
from .result_cache import cache_query_result, estimate_result_tokens

logger = logging.getLogger(__name__)

def detect_aggregation_failure(query: str, result: Dict[str, Any]) -> bool:
    """Detect if query failed due to COUNT/GROUP BY returning IRIs instead of numbers.
    
    Args:
        query: The SPARQL query that was executed
        result: The query result
        
    Returns:
        True if aggregation failure detected, False otherwise
    """
    # Check if query contains COUNT with GROUP BY
    query_upper = query.upper()
    has_count = "COUNT(" in query_upper
    has_group_by = "GROUP BY" in query_upper
    
    if not (has_count and has_group_by):
        return False
    
    # Check if result has the expected structure
    if "status" not in result or result["status"] != "success":
        return False
    
    if "data" not in result or "results" not in result["data"]:
        return False
    
    results = result["data"]["results"]
    if not results:
        return False
    
    # Check if any COUNT column contains an IRI instead of a number
    for row in results:
        for value in row:
            # Look for values that should be numbers but are IRIs
            if isinstance(value, str) and value.startswith("http"):
                # This is likely a COUNT that returned an IRI
                return True
    
    return False

def rewrite_for_python_aggregation(query: str) -> str:
    """Rewrite a COUNT/GROUP BY query to fetch raw data for Python aggregation.
    
    Args:
        query: The original SPARQL query with COUNT/GROUP BY
        
    Returns:
        Simplified query that fetches raw data
    """
    # Remove COUNT() and keep the variable being counted
    # Pattern: COUNT(DISTINCT ?var) AS ?count -> ?var
    query = re.sub(r'COUNT\s*\(\s*(?:DISTINCT\s+)?(\?[\w]+)\s*\)\s*(?:AS\s+\?[\w]+)?', r'\1', query, flags=re.IGNORECASE)
    
    # Remove GROUP BY clause
    query = re.sub(r'GROUP\s+BY\s+[^)]+?(?=ORDER|LIMIT|$)', '', query, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    
    # Remove aggregation aliases in SELECT
    query = re.sub(r'\(\s*(\?[\w]+)\s+AS\s+\?[\w]+\s*\)', r'\1', query, flags=re.IGNORECASE)
    
    # Clean up any duplicate spaces
    query = re.sub(r'\s+', ' ', query)
    
    return query.strip()

class SPARQLExecutor:
    """Handles SPARQL query execution with caching."""
    
    def __init__(self):
        self.config = get_sparql_config()
        self.cache_file = CACHE_DIR / "query_cache.json"
        self.pattern_file = CACHE_DIR / "successful_patterns.json"
        self.load_cache()
    
    def load_cache(self):
        """Load query cache and patterns from disk."""
        self.query_cache = {}
        self.successful_patterns = []
        
        if CACHE_ENABLED and self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self.query_cache = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load query cache: {e}")
        
        if self.pattern_file.exists():
            try:
                with open(self.pattern_file, 'r') as f:
                    self.successful_patterns = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load patterns: {e}")
    
    def save_cache(self):
        """Save query cache and patterns to disk."""
        if CACHE_ENABLED:
            try:
                with open(self.cache_file, 'w') as f:
                    json.dump(self.query_cache, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save query cache: {e}")
        
        try:
            with open(self.pattern_file, 'w') as f:
                json.dump(self.successful_patterns, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")
    
    def get_query_hash(self, query: str) -> str:
        """Generate hash for query caching."""
        return hashlib.sha256(query.strip().encode()).hexdigest()
    
    def execute(self, query: str) -> Dict[str, Any]:
        """Execute SPARQL query with caching."""
        query_hash = self.get_query_hash(query)
        
        # Check cache
        if CACHE_ENABLED and query_hash in self.query_cache:
            logger.info("Returning cached result")
            return self.query_cache[query_hash]
        
        # Execute query
        try:
            response = requests.post(
                self.config["endpoint"],
                json={
                    "query": query,
                    "use_names": True,
                    "timeout": self.config["timeout"]
                },
                headers={"Content-Type": "application/json"},
                timeout=self.config["timeout"]
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Cache successful result
                if CACHE_ENABLED:
                    self.query_cache[query_hash] = result
                    self.save_cache()
                
                # Learn from successful pattern
                self.learn_pattern(query, result)
                
                return result
            else:
                return {
                    "error": f"Query failed with status {response.status_code}",
                    "details": response.text
                }
        
        except requests.exceptions.Timeout:
            return {"error": "Query timeout", "timeout": self.config["timeout"]}
        except Exception as e:
            return {"error": str(e)}
    
    def learn_pattern(self, query: str, result: Dict[str, Any]):
        """Learn from successful query patterns."""
        if "results" in result and result["results"].get("bindings"):
            pattern = {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "result_count": len(result["results"]["bindings"]),
                "variables": result["head"]["vars"] if "head" in result else []
            }
            
            # Classify pattern
            if "SELECT" in query.upper():
                if "AVG(" in query or "MIN(" in query or "MAX(" in query:
                    pattern["type"] = "aggregation"
                elif "GROUP BY" in query:
                    pattern["type"] = "grouping"
                else:
                    pattern["type"] = "simple_select"
            
            self.successful_patterns.append(pattern)
            
            # Keep only last 100 patterns
            if len(self.successful_patterns) > 100:
                self.successful_patterns = self.successful_patterns[-100:]
            
            self.save_cache()

# Create singleton instance
executor = SPARQLExecutor()

def execute_sparql(query: str) -> Dict[str, Any]:
    """Execute SPARQL query with caching and learning.
    
    Args:
        query: SPARQL query to execute
    
    Returns:
        Query results or error information
    """
    logger.info(f"Executing SPARQL query: {query[:100]}...")
    
    result = executor.execute(query)
    
    # Handle all successful results by caching them
    if "status" in result and result["status"] == "success":
        # Check for aggregation failure (COUNT/GROUP BY returning IRIs)
        if detect_aggregation_failure(query, result):
            logger.warning("Detected COUNT/GROUP BY aggregation failure - IRIs returned instead of numbers")
            
            # Rewrite query for Python aggregation
            rewritten_query = rewrite_for_python_aggregation(query)
            
            result["aggregation_failure"] = True
            result["fallback_query"] = rewritten_query
            result["fallback_suggestion"] = (
                "The SPARQL engine returned IRIs instead of numbers for COUNT/GROUP BY. "
                "Use the fallback_query to fetch raw data and aggregate with Python using analyze_patterns tool."
            )
        
        # Estimate tokens to decide if we need to return summary
        estimated_tokens = estimate_result_tokens(result)
        
        # Always cache the result
        cache_id, summary = cache_query_result(query, result)
        
        # If result is large (>10k tokens), return summary instead of full result
        if estimated_tokens > 10000:
            logger.info(f"Large result ({estimated_tokens} tokens) cached as {cache_id}")
            return {
                "status": "success",
                "summary": summary,
                "warning": f"Result contains ~{estimated_tokens} tokens. Returning summary to prevent token overflow.",
                "cache_id": cache_id,
                "full_result_available": True
            }
        else:
            # For smaller results, still cache but return full data
            result["cache_id"] = cache_id
            return result
    
    return result

def get_successful_patterns() -> list:
    """Get list of successful query patterns for learning."""
    return executor.successful_patterns

def get_cached_query_result(cache_id: str) -> Dict[str, Any]:
    """Retrieve full cached query result by ID.
    
    Args:
        cache_id: The cache ID returned from a previous query
        
    Returns:
        Full query result or error if not found
    """
    from .result_cache import get_cached_result
    
    result = get_cached_result(cache_id)
    if result:
        return result
    else:
        return {
            "status": "error",
            "error": f"No cached result found for ID: {cache_id}"
        }