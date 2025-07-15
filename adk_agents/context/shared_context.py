from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import hashlib

class SharedAgentContext:
    """Manages shared context between agents"""
    
    def __init__(self):
        self.discovered_properties: Dict[str, Dict[str, Any]] = {}
        self.query_results: Dict[str, Any] = {}
        self.data_patterns: Dict[str, Any] = {}
        self.known_issues: List[Dict[str, str]] = []
        self.successful_queries: List[Dict[str, Any]] = []
        self.failed_queries: List[Dict[str, Any]] = []
        
    def cache_property_discovery(self, class_name: str, properties: List[Dict]):
        """Cache discovered properties for a class"""
        self.discovered_properties[class_name] = {
            "properties": properties,
            "discovered_at": datetime.now().isoformat(),
            "data_types": self._extract_data_types(properties)
        }
    
    def get_cached_properties(self, class_name: str) -> Optional[Dict]:
        """Retrieve cached properties for a class"""
        return self.discovered_properties.get(class_name)
    
    def cache_query_result(self, query: str, result: Dict, purpose: str):
        """Cache query results with metadata"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        self.query_results[query_hash] = {
            "query": query,
            "result": result,
            "purpose": purpose,
            "cached_at": datetime.now().isoformat(),
            "row_count": result.get("row_count", 0)
        }
    
    def get_cached_query_result(self, query: str) -> Optional[Dict]:
        """Get cached result for a query"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return self.query_results.get(query_hash)
    
    def record_known_issue(self, issue_type: str, details: str, workaround: str):
        """Record known issues and workarounds"""
        self.known_issues.append({
            "type": issue_type,
            "details": details,
            "workaround": workaround,
            "recorded_at": datetime.now().isoformat()
        })
    
    def add_successful_query(self, query: str, results: Any, purpose: str = ""):
        """Record a successful query pattern"""
        self.successful_queries.append({
            "query": query,
            "row_count": len(results) if isinstance(results, list) else 0,
            "purpose": purpose,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only last 50 successful queries
        self.successful_queries = self.successful_queries[-50:]
    
    def add_failed_query(self, query: str, error: str):
        """Record a failed query for analysis"""
        self.failed_queries.append({
            "query": query,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only last 20 failed queries
        self.failed_queries = self.failed_queries[-20:]
    
    def add_discovered_entity(self, entity_type: str, entity_name: str):
        """Add a discovered entity to the patterns"""
        if entity_type not in self.data_patterns:
            self.data_patterns[entity_type] = []
        if entity_name not in self.data_patterns[entity_type]:
            self.data_patterns[entity_type].append(entity_name)
    
    def get_query_patterns(self) -> List[Dict[str, Any]]:
        """Get successful query patterns for reuse"""
        patterns = []
        for query_info in self.successful_queries[-10:]:
            if query_info["row_count"] > 0:
                patterns.append({
                    "query": query_info["query"],
                    "purpose": query_info["purpose"],
                    "row_count": query_info["row_count"]
                })
        return patterns
    
    def _extract_data_types(self, properties: List[Dict]) -> Dict[str, str]:
        """Extract data types from property list"""
        data_types = {}
        for prop in properties:
            if isinstance(prop, dict):
                prop_name = prop.get("property", "")
                prop_type = prop.get("type", "unknown")
                if prop_name:
                    data_types[prop_name] = prop_type
        return data_types
    
    def to_dict(self) -> Dict:
        """Serialize context for state storage"""
        return {
            "discovered_properties": self.discovered_properties,
            "query_results": list(self.query_results.values())[-20:],  # Keep last 20
            "data_patterns": self.data_patterns,
            "known_issues": self.known_issues,
            "successful_queries": self.successful_queries[-10:],
            "failed_queries": self.failed_queries[-5:]
        }
    
    @classmethod
    def from_state(cls, state: Dict) -> 'SharedAgentContext':
        """Reconstruct from state"""
        context = cls()
        shared_data = state.get("_shared_context", {})
        context.discovered_properties = shared_data.get("discovered_properties", {})
        context.data_patterns = shared_data.get("data_patterns", {})
        context.known_issues = shared_data.get("known_issues", [])
        context.successful_queries = shared_data.get("successful_queries", [])
        context.failed_queries = shared_data.get("failed_queries", [])
        
        # Reconstruct query_results dict from list
        if "query_results" in shared_data:
            for result in shared_data["query_results"]:
                if isinstance(result, dict) and "query" in result:
                    query_hash = hashlib.md5(result["query"].encode()).hexdigest()
                    context.query_results[query_hash] = result
        
        return context
    
    def get_summary(self) -> str:
        """Get a summary of the current context"""
        return f"""
        Shared Context Summary:
        - Discovered classes: {len(self.discovered_properties)}
        - Cached query results: {len(self.query_results)}
        - Known entity types: {list(self.data_patterns.keys())}
        - Known issues: {len(self.known_issues)}
        - Successful queries: {len(self.successful_queries)}
        - Failed queries: {len(self.failed_queries)}
        """