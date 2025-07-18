"""
SPARQL Tool for Google ADK - executes queries against MES ontology.
"""
import asyncio
import json
import hashlib
from typing import Dict, List, Optional, Any
import aiohttp
from google.adk.tools import FunctionTool, ToolContext
from pydantic import BaseModel, Field

from ..config.settings import SPARQL_ENDPOINT, SPARQL_TIMEOUT
from ..utils.owlready2_adapter import adapt_sparql_for_owlready2, format_owlready2_results
from ..utils.result_manager import ResultManager
from ..utils.rate_limiter import get_rate_limiter


class SPARQLQueryParams(BaseModel):
    """Parameters for SPARQL query execution."""
    query: str = Field(..., description="SPARQL query to execute")
    parameters: Optional[List[str]] = Field(None, description="Query parameters")
    timeout: int = Field(SPARQL_TIMEOUT, description="Query timeout in milliseconds")
    adapt_for_owlready2: bool = Field(True, description="Adapt query for Owlready2 compatibility")


async def execute_sparql_query(
    tool_context: ToolContext,
    query: str,
    parameters: Optional[List[str]] = None,
    timeout: int = SPARQL_TIMEOUT,
    adapt_for_owlready2: bool = True,
    purpose: Optional[str] = None,
    analysis_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute SPARQL query against the MES ontology with ADK state management.
    
    Args:
        tool_context: ADK ToolContext for state and artifact management
        query: SPARQL query string
        parameters: Optional query parameters
        timeout: Query timeout in seconds
        adapt_for_owlready2: Whether to adapt query for Owlready2
        purpose: Description of query purpose for caching
        analysis_type: Type of analysis for better cache matching
    
    Returns:
        Dictionary containing query results or error information
    """
    try:
        # Initialize result manager
        result_manager = ResultManager(tool_context)
        
        # Generate query ID for caching
        query_id = hashlib.md5(f"{query}:{parameters}".encode()).hexdigest()[:12]
        
        # Check cache in ADK state
        cache_key = f"app:query_cache:{query_id}"
        if cache_key in tool_context.state and purpose:
            cached_result = tool_context.state[cache_key]
            return {
                "success": True,
                "results": cached_result["results"],
                "query": cached_result["query"],
                "row_count": cached_result["row_count"],
                "cached": True,
                "cache_key": cache_key
            }
        
        # Adapt query if needed
        if adapt_for_owlready2:
            adapted_query = adapt_sparql_for_owlready2(query)
        else:
            adapted_query = query
        
        # Prepare request payload
        payload = {
            "query": adapted_query,
            "timeout": timeout
        }
        
        if parameters:
            payload["parameters"] = parameters
        
        # Execute query with rate limiting
        rate_limiter = get_rate_limiter()
        await rate_limiter.acquire()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                SPARQL_ENDPOINT,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                
                if response.status == 200:
                    results = await response.json()
                    
                    # Format results for consistency
                    formatted_results = format_owlready2_results(results)
                    
                    # Store results using ResultManager for large datasets
                    if len(formatted_results) > 100:
                        storage_info = await result_manager.store_result(
                            query_id=query_id,
                            result=formatted_results,
                            query=adapted_query,
                            metadata={
                                "purpose": purpose,
                                "analysis_type": analysis_type
                            }
                        )
                        
                        # Return summary for large results
                        return {
                            "success": True,
                            "results": formatted_results[:10],  # Preview only
                            "query": adapted_query,
                            "row_count": len(formatted_results),
                            "cached": False,
                            "storage": storage_info,
                            "full_results_available": True,
                            "preview_note": f"Showing first 10 of {len(formatted_results)} rows. Full results stored as {storage_info['storage_type']}."
                        }
                    
                    # Cache successful queries in ADK state
                    if purpose and formatted_results:
                        tool_context.state[cache_key] = {
                            "query": adapted_query,
                            "results": formatted_results,
                            "row_count": len(formatted_results),
                            "purpose": purpose,
                            "analysis_type": analysis_type
                        }
                    
                    return {
                        "success": True,
                        "results": formatted_results,
                        "query": adapted_query,
                        "row_count": len(formatted_results),
                        "cached": False
                    }
                else:
                    error_text = await response.text()
                    
                    # Record failure in state
                    failure_key = f"temp:query_failure:{query_id}"
                    tool_context.state[failure_key] = {
                        "query": adapted_query,
                        "error": error_text,
                        "status_code": response.status
                    }
                    
                    # Attempt common fixes
                    if "Unknown prefix" in error_text:
                        fixed_query = query.replace("mes:", "mes_ontology_populated:")
                        return await execute_sparql_query(
                            tool_context, fixed_query, parameters, timeout, 
                            adapt_for_owlready2, purpose, analysis_type
                        )
                    
                    # Return structured error for LLM to learn from
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "query": adapted_query,
                        "suggestion": "Check query syntax, ensure proper use of mes_ontology_populated: prefix"
                    }
                    
    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": f"Query timeout after {timeout}ms",
            "query": adapted_query if 'adapted_query' in locals() else query
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Query execution failed: {str(e)}",
            "query": adapted_query if 'adapted_query' in locals() else query
        }


# Create the ADK tool
sparql_tool = FunctionTool(execute_sparql_query)


# Essential discovery helper
async def discover_equipment_instances(tool_context: ToolContext) -> Dict[str, Any]:
    """Discover all equipment instances in the ontology."""
    query = """SELECT DISTINCT ?equipment ?type WHERE {
        ?equipment a ?type .
        ?type rdfs:subClassOf* mes_ontology_populated:Equipment .
        FILTER(ISIRI(?equipment))
        FILTER(ISIRI(?type))
    }
    ORDER BY ?equipment"""
    
    return await execute_sparql_query(
        tool_context,
        query,
        purpose="Discover equipment instances",
        analysis_type="discovery"
    )


# Core analysis helper
async def query_underperforming_equipment(
    tool_context: ToolContext,
    oee_threshold: float = 85.0
) -> Dict[str, Any]:
    """Find equipment with OEE below threshold."""
    query = f"""
    SELECT DISTINCT ?equipment ?equipmentID ?avgOEE
    WHERE {{
        ?equipment mes_ontology_populated:logsEvent ?event .
        ?event a mes_ontology_populated:ProductionLog .
        ?equipment mes_ontology_populated:hasEquipmentID ?equipmentID .
        ?event mes_ontology_populated:hasOEEScore ?oee .
        
        FILTER(?oee < {oee_threshold})
    }}
    """
    
    return await execute_sparql_query(
        tool_context,
        query,
        purpose=f"Find equipment with OEE below {oee_threshold}%",
        analysis_type="performance"
    )