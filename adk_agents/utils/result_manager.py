"""
Result Manager for ADK Agents

Handles storage and retrieval of SPARQL query results using ADK's state and artifact management.
Large results (>100 rows) are stored as artifacts, while small results are stored in state.
"""

import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging

from google.adk.tools import ToolContext


logger = logging.getLogger(__name__)


class ResultManager:
    """
    Manages SPARQL query results using ADK state and artifact patterns.
    
    Features:
    - Stores large results (>100 rows) as artifacts
    - Stores small results in state with temp: prefix
    - Provides summaries for LLM context
    - Handles async artifact operations
    """
    
    def __init__(self, tool_context: ToolContext, row_threshold: int = 100):
        """
        Initialize ResultManager with ADK ToolContext.
        
        Args:
            tool_context: ADK ToolContext for state/artifact management
            row_threshold: Number of rows above which results are stored as artifacts
        """
        self.tool_context = tool_context
        self.row_threshold = row_threshold
        
    async def store_result(
        self, 
        query_id: str, 
        result: List[Dict[str, Any]], 
        query: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store query result using appropriate storage method based on size.
        
        Args:
            query_id: Unique identifier for the query
            result: List of result rows
            query: The SPARQL query that produced this result
            metadata: Optional metadata about the query/result
            
        Returns:
            Storage info including method used and location
        """
        result_info = {
            "query_id": query_id,
            "row_count": len(result),
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "metadata": metadata or {}
        }
        
        if len(result) > self.row_threshold:
            # Store as artifact for large results
            artifact_name = f"sparql_result_{query_id}.json"
            artifact_data = {
                "query": query,
                "result": result,
                "metadata": result_info
            }
            
            # Save artifact asynchronously
            await self.tool_context.save_artifact(
                name=artifact_name,
                data=json.dumps(artifact_data, indent=2)
            )
            
            # Store reference in state
            state_key = f"temp:result_ref:{query_id}"
            self.tool_context.state[state_key] = {
                "storage_type": "artifact",
                "artifact_name": artifact_name,
                **result_info
            }
            
            logger.info(f"Stored large result ({len(result)} rows) as artifact: {artifact_name}")
            
            return {
                "storage_type": "artifact",
                "artifact_name": artifact_name,
                "row_count": len(result)
            }
            
        else:
            # Store directly in state for small results
            state_key = f"temp:result_data:{query_id}"
            self.tool_context.state[state_key] = {
                "storage_type": "state",
                "data": result,
                **result_info
            }
            
            logger.info(f"Stored small result ({len(result)} rows) in state: {state_key}")
            
            return {
                "storage_type": "state",
                "state_key": state_key,
                "row_count": len(result)
            }
    
    async def get_result(self, query_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve stored result by query ID.
        
        Args:
            query_id: The query identifier
            
        Returns:
            The result data or None if not found
        """
        # Check state reference first
        ref_key = f"temp:result_ref:{query_id}"
        data_key = f"temp:result_data:{query_id}"
        
        if ref_key in self.tool_context.state:
            # Result stored as artifact
            ref_info = self.tool_context.state[ref_key]
            artifact_name = ref_info["artifact_name"]
            
            # Load artifact asynchronously
            artifact_data = await self.tool_context.load_artifact(artifact_name)
            if artifact_data:
                data = json.loads(artifact_data)
                return data["result"]
                
        elif data_key in self.tool_context.state:
            # Result stored in state
            return self.tool_context.state[data_key]["data"]
            
        return None
    
    def get_result_summary(
        self, 
        query_id: str, 
        max_rows: int = 10,
        include_query: bool = True
    ) -> Dict[str, Any]:
        """
        Get a summary of stored result suitable for LLM context.
        
        Args:
            query_id: The query identifier
            max_rows: Maximum number of rows to include in summary
            include_query: Whether to include the original query
            
        Returns:
            Summary dict with truncated results and metadata
        """
        # Check both storage types
        ref_key = f"temp:result_ref:{query_id}"
        data_key = f"temp:result_data:{query_id}"
        
        if ref_key in self.tool_context.state:
            # Summary for artifact-stored result
            ref_info = self.tool_context.state[ref_key]
            summary = {
                "query_id": query_id,
                "storage_type": "artifact",
                "total_rows": ref_info["row_count"],
                "timestamp": ref_info["timestamp"],
                "artifact_name": ref_info["artifact_name"],
                "preview_note": f"Full result ({ref_info['row_count']} rows) stored as artifact"
            }
            
            if include_query:
                summary["query"] = ref_info["query"]
                
            if ref_info.get("metadata"):
                summary["metadata"] = ref_info["metadata"]
                
            return summary
            
        elif data_key in self.tool_context.state:
            # Summary for state-stored result
            state_data = self.tool_context.state[data_key]
            result_data = state_data["data"]
            
            summary = {
                "query_id": query_id,
                "storage_type": "state",
                "total_rows": len(result_data),
                "timestamp": state_data["timestamp"],
                "rows_shown": min(len(result_data), max_rows),
                "data": result_data[:max_rows]
            }
            
            if len(result_data) > max_rows:
                summary["truncated"] = True
                summary["truncated_rows"] = len(result_data) - max_rows
                
            if include_query:
                summary["query"] = state_data["query"]
                
            if state_data.get("metadata"):
                summary["metadata"] = state_data["metadata"]
                
            return summary
            
        return {
            "query_id": query_id,
            "error": "Result not found"
        }
    
    def list_stored_results(self) -> List[Dict[str, Any]]:
        """
        List all stored results with their metadata.
        
        Returns:
            List of result summaries
        """
        results = []
        
        # Find all result references in state
        for key, value in self.tool_context.state.items():
            if key.startswith("temp:result_ref:") or key.startswith("temp:result_data:"):
                query_id = key.split(":")[-1]
                
                if key.startswith("temp:result_ref:"):
                    # Artifact reference
                    results.append({
                        "query_id": query_id,
                        "storage_type": "artifact",
                        "row_count": value["row_count"],
                        "timestamp": value["timestamp"],
                        "artifact_name": value["artifact_name"]
                    })
                else:
                    # State data
                    results.append({
                        "query_id": query_id,
                        "storage_type": "state",
                        "row_count": value["row_count"],
                        "timestamp": value["timestamp"]
                    })
                    
        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return results
    
    def clear_result(self, query_id: str) -> bool:
        """
        Clear a stored result from state/artifacts.
        
        Args:
            query_id: The query identifier
            
        Returns:
            True if cleared, False if not found
        """
        ref_key = f"temp:result_ref:{query_id}"
        data_key = f"temp:result_data:{query_id}"
        
        cleared = False
        
        if ref_key in self.tool_context.state:
            # Note: Artifact deletion would need to be handled separately
            # as ADK doesn't provide direct artifact deletion in the examples
            del self.tool_context.state[ref_key]
            cleared = True
            logger.info(f"Cleared artifact reference for query: {query_id}")
            
        if data_key in self.tool_context.state:
            del self.tool_context.state[data_key]
            cleared = True
            logger.info(f"Cleared state data for query: {query_id}")
            
        return cleared
    
    def clear_all_results(self) -> int:
        """
        Clear all stored results from state.
        
        Returns:
            Number of results cleared
        """
        keys_to_delete = []
        
        # Find all result keys
        for key in self.tool_context.state.keys():
            if key.startswith("temp:result_ref:") or key.startswith("temp:result_data:"):
                keys_to_delete.append(key)
                
        # Delete all found keys
        for key in keys_to_delete:
            del self.tool_context.state[key]
            
        logger.info(f"Cleared {len(keys_to_delete)} stored results")
        
        return len(keys_to_delete)
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored results.
        
        Returns:
            Dict with storage statistics
        """
        artifact_count = 0
        state_count = 0
        total_rows = 0
        
        for key, value in self.tool_context.state.items():
            if key.startswith("temp:result_ref:"):
                artifact_count += 1
                total_rows += value["row_count"]
            elif key.startswith("temp:result_data:"):
                state_count += 1
                total_rows += value["row_count"]
                
        return {
            "total_results": artifact_count + state_count,
            "artifact_stored": artifact_count,
            "state_stored": state_count,
            "total_rows": total_rows,
            "row_threshold": self.row_threshold
        }