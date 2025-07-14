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
from ..agents.orchestrator import shared_context


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
        timeout: Query timeout in seconds
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
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                
                if response.status == 200:
                    results = await response.json()
                    
                    # Format results for consistency
                    formatted_results = format_owlready2_results(results)
                    
                    # Record successful query in shared context
                    if formatted_results:
                        shared_context.add_successful_query(
                            adapted_query, 
                            formatted_results,
                            purpose=f"Retrieved {len(formatted_results)} results"
                        )
                    
                    return {
                        "success": True,
                        "results": formatted_results,
                        "query": adapted_query,
                        "row_count": len(formatted_results)
                    }
                else:
                    error_text = await response.text()
                    
                    # Record failed query in shared context
                    shared_context.add_failed_query(adapted_query, error_text)
                    
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
# FunctionTool automatically extracts metadata from the function's docstring and annotations
sparql_tool = FunctionTool(execute_sparql_query)


# Discovery queries for ontology exploration
async def discover_classes() -> Dict[str, Any]:
    """Discover all classes in the ontology."""
    query = """
    SELECT DISTINCT ?class WHERE {
        ?class a owl:Class .
        FILTER(ISIRI(?class))
    }
    ORDER BY ?class
    """
    return await execute_sparql_query(query)


async def discover_equipment_instances() -> Dict[str, Any]:
    """Discover all equipment instances in the ontology."""
    query = """
    SELECT DISTINCT ?equipment ?type WHERE {
        ?equipment a ?type .
        ?type rdfs:subClassOf* mes_ontology_populated:Equipment .
        FILTER(ISIRI(?equipment))
        FILTER(ISIRI(?type))
    }
    ORDER BY ?equipment
    """
    result = await execute_sparql_query(query)
    
    # Add discovered equipment to shared context
    if result.get('success') and result.get('results'):
        for row in result['results']:
            if len(row) >= 1:
                equipment = str(row[0]).split('#')[-1] if '#' in str(row[0]) else str(row[0])
                shared_context.add_discovered_entity('equipment', equipment)
    
    return result


async def discover_properties_for_class(class_name: str) -> Dict[str, Any]:
    """Discover all properties associated with instances of a class."""
    query = f"""
    SELECT DISTINCT ?property WHERE {{
        ?instance a mes_ontology_populated:{class_name} .
        ?instance ?property ?value .
        FILTER(ISIRI(?property))
    }}
    ORDER BY ?property
    """
    return await execute_sparql_query(query)


async def discover_entity_properties(entity_uri: str) -> Dict[str, Any]:
    """Discover all properties and values for a specific entity."""
    query = """
    SELECT ?property ?value WHERE {
        ?? ?property ?value .
        FILTER(ISIRI(?property))
    }
    ORDER BY ?property
    """
    return await execute_sparql_query(query, parameters=[entity_uri])


async def validate_entity_exists(entity_uri: str) -> Dict[str, Any]:
    """Check if an entity exists in the ontology."""
    query = """
    SELECT ?type WHERE {
        ?? a ?type .
        FILTER(ISIRI(?type))
    }
    LIMIT 1
    """
    return await execute_sparql_query(query, parameters=[entity_uri])


# Helper functions for common queries
async def query_underperforming_equipment(oee_threshold: float = 85.0) -> Dict[str, Any]:
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
    return await execute_sparql_query(query)


async def query_equipment_downtime(equipment_id: str) -> Dict[str, Any]:
    """Get downtime events for specific equipment."""
    query = f"""
    SELECT ?timestamp ?reasonCode
    WHERE {{
        ?equipment mes_ontology_populated:hasEquipmentID "{equipment_id}" .
        ?equipment mes_ontology_populated:logsEvent ?event .
        ?event a mes_ontology_populated:DowntimeLog .
        ?event mes_ontology_populated:hasTimestamp ?timestamp .
        OPTIONAL {{ ?event mes_ontology_populated:hasDowntimeReasonCode ?reasonCode }}
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
        ?equipment mes_ontology_populated:logsEvent ?event .
        ?event a mes_ontology_populated:ProductionLog .
        ?order mes_ontology_populated:producesProduct ?product .
        ?product mes_ontology_populated:hasProductName "{product_name}" .
        ?equipment mes_ontology_populated:executesOrder ?order .
        ?event mes_ontology_populated:hasQualityScore ?qualityScore .
        ?event mes_ontology_populated:hasScrapUnits ?scrap .
        ?event mes_ontology_populated:hasGoodUnits ?good .
        ?event mes_ontology_populated:hasTimestamp ?timestamp .
        
        BIND((?scrap / (?good + ?scrap)) AS ?scrapRate)
    }}
    ORDER BY DESC(?timestamp)
    LIMIT 100
    """
    return await execute_sparql_query(query)