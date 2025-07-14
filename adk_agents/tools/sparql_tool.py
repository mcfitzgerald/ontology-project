"""
SPARQL Tool for Google ADK - executes queries against MES ontology.
"""
import asyncio
import json
from typing import Dict, List, Optional, Any
import aiohttp
from google.adk.tools import FunctionTool
from pydantic import BaseModel, Field

from ..config.settings import SPARQL_ENDPOINT, SPARQL_TIMEOUT
from ..utils.owlready2_adapter import adapt_sparql_for_owlready2, format_owlready2_results


class SPARQLQueryParams(BaseModel):
    """Parameters for SPARQL query execution."""
    query: str = Field(..., description="SPARQL query to execute")
    parameters: Optional[List[str]] = Field(None, description="Query parameters")
    timeout: int = Field(SPARQL_TIMEOUT, description="Query timeout in milliseconds")
    adapt_for_owlready2: bool = Field(True, description="Adapt query for Owlready2 compatibility")


async def execute_sparql_query(
    query: str,
    parameters: Optional[List[str]] = None,
    timeout: int = SPARQL_TIMEOUT,
    adapt_for_owlready2: bool = True
) -> Dict[str, Any]:
    """
    Execute SPARQL query against the MES ontology.
    
    Args:
        query: SPARQL query string
        parameters: Optional query parameters
        timeout: Query timeout in milliseconds
        adapt_for_owlready2: Whether to adapt query for Owlready2
    
    Returns:
        Dictionary containing query results or error information
    """
    try:
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
        
        # Execute query
        async with aiohttp.ClientSession() as session:
            async with session.post(
                SPARQL_ENDPOINT,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout/1000)
            ) as response:
                
                if response.status == 200:
                    results = await response.json()
                    
                    # Format results for consistency
                    formatted_results = format_owlready2_results(results)
                    
                    return {
                        "success": True,
                        "results": formatted_results,
                        "query": adapted_query,
                        "row_count": len(formatted_results)
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "query": adapted_query
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
sparql_tool = FunctionTool(
    func=execute_sparql_query,
    name="sparql_query",
    description="""Execute SPARQL queries against the manufacturing ontology.
    
    Automatically adapts queries for Owlready2 compatibility:
    - Removes PREFIX declarations
    - Removes angle brackets
    - Adds FILTER(ISIRI()) where needed
    - Converts property syntax
    
    Returns query results in a consistent format with success/error status.""",
    input_schema=SPARQLQueryParams
)


# Helper functions for common queries
async def query_underperforming_equipment(oee_threshold: float = 85.0) -> Dict[str, Any]:
    """Find equipment with OEE below threshold."""
    query = f"""
    SELECT DISTINCT ?equipment ?equipmentID ?avgOEE
    WHERE {{
        ?event a mes:ProductionLog .
        ?event mes:logsEquipment ?equipment .
        ?equipment mes:hasEquipmentID ?equipmentID .
        ?event mes:hasOEEScore ?oee .
        
        FILTER(?oee < {oee_threshold})
    }}
    """
    return await execute_sparql_query(query)


async def query_equipment_downtime(equipment_id: str) -> Dict[str, Any]:
    """Get downtime events for specific equipment."""
    query = f"""
    SELECT ?timestamp ?reason ?duration
    WHERE {{
        ?event a mes:DowntimeLog .
        ?event mes:logsEquipment ?equipment .
        ?equipment mes:hasEquipmentID "{equipment_id}" .
        ?event mes:hasTimestamp ?timestamp .
        ?event mes:hasDowntimeReason ?reason .
        ?event mes:hasDowntimeDuration ?duration .
    }}
    ORDER BY DESC(?timestamp)
    LIMIT 100
    """
    return await execute_sparql_query(query)


async def query_product_quality(product_name: str) -> Dict[str, Any]:
    """Get quality metrics for a specific product."""
    query = f"""
    SELECT ?equipment ?qualityScore ?scrapRate ?timestamp
    WHERE {{
        ?event a mes:ProductionLog .
        ?event mes:producesProduct ?product .
        ?product mes:hasProductName "{product_name}" .
        ?event mes:logsEquipment ?equipment .
        ?event mes:hasQualityScore ?qualityScore .
        ?event mes:hasScrapUnitsProduced ?scrap .
        ?event mes:hasGoodUnitsProduced ?good .
        ?event mes:hasTimestamp ?timestamp .
        
        BIND((?scrap / (?good + ?scrap)) AS ?scrapRate)
    }}
    ORDER BY DESC(?timestamp)
    LIMIT 100
    """
    return await execute_sparql_query(query)