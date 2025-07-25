"""SPARQL execution tool with caching and pattern learning."""
import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
from pathlib import Path
import logging
from ..config.settings import (
    SPARQL_ENDPOINT, SPARQL_TIMEOUT, SPARQL_MAX_RESULTS,
    CACHE_DIR, CACHE_ENABLED, get_sparql_config
)
from .result_cache import cache_query_result, estimate_result_tokens

logger = logging.getLogger(__name__)

class SPARQLExecutor:
    """Handles SPARQL query execution with caching."""
    
    def __init__(self):
        self.config = get_sparql_config()
        self.cache_file = CACHE_DIR / "query_cache.json"
        self.load_cache()
    
    def load_cache(self):
        """Load query cache from disk."""
        self.query_cache = {}
        
        if CACHE_ENABLED and self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self.query_cache = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load query cache: {e}")
    
    def save_cache(self):
        """Save query cache to disk."""
        if CACHE_ENABLED:
            try:
                with open(self.cache_file, 'w') as f:
                    json.dump(self.query_cache, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save query cache: {e}")
    
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
        # Always provide a sample for LLM assessment
        if "data" in result and "results" in result["data"]:
            data = result["data"]
            total_rows = len(data["results"])
            
            # Create sample for LLM (first 5 rows)
            sample_size = min(5, total_rows)
            result["data_sample"] = {
                "columns": data.get("columns", []),
                "rows": data["results"][:sample_size],
                "total_rows": total_rows
            }
        
        # Let the LLM handle any aggregation issues using its context knowledge
        # Estimate tokens to decide if we need to return summary
        estimated_tokens = estimate_result_tokens(result)
        
        # Always cache the result
        cache_id, summary = cache_query_result(query, result)
        
        # For large results, return summary + sample
        if estimated_tokens > 10000:
            logger.info(f"Large result ({estimated_tokens} tokens) cached as {cache_id}")
            
            return {
                "status": "success",
                "data_sample": result.get("data_sample", {}),
                "summary": {
                    "total_rows": total_rows,
                    "columns": data.get("columns", []),
                    "cache_id": cache_id,
                    "estimated_tokens": estimated_tokens
                },
                "full_result_cached": True,
                "python_hint": f"Use execute_python_code with cache_id='{cache_id}'. DataFrame 'df' will be pre-loaded with columns: {data.get('columns', [])}"
            }
        else:
            # For smaller results, still cache but return full data
            result["cache_id"] = cache_id
            return result
    
    return result

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