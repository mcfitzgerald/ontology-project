"""SPARQL execution tool with caching and pattern learning."""
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
from pathlib import Path
import logging
from google.genai import types

from ..config.settings import (
    SPARQL_ENDPOINT, SPARQL_TIMEOUT, SPARQL_MAX_RESULTS,
    CACHE_DIR, CACHE_ENABLED, get_sparql_config
)

logger = logging.getLogger(__name__)

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
                data={"query": query},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
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

def execute_sparql(query: str, tool_context: types.ToolContext) -> Dict[str, Any]:
    """Execute SPARQL query with caching and learning.
    
    Args:
        query: SPARQL query to execute
        tool_context: ADK tool context
    
    Returns:
        Query results or error information
    """
    logger.info(f"Executing SPARQL query: {query[:100]}...")
    
    result = executor.execute(query)
    
    # Handle large results
    if "results" in result and len(str(result)) > 50000:
        # Create artifact for large results
        bindings = result["results"]["bindings"]
        summary = {
            "status": "success",
            "result_count": len(bindings),
            "variables": result["head"]["vars"],
            "sample_results": bindings[:10],
            "note": "Full results saved as artifact due to size"
        }
        
        # In real implementation, would create artifact here
        # For now, just return summary
        return summary
    
    return result

def get_successful_patterns() -> list:
    """Get list of successful query patterns for learning."""
    return executor.successful_patterns