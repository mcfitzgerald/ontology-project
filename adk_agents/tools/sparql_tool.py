"""
SPARQL Tool for Google ADK - executes queries against MES ontology.
"""
import asyncio
import json
from typing import Dict, List, Optional, Any
import aiohttp
from google.adk.tools import FunctionTool
from pydantic import BaseModel, Field

from ..config.settings import SPARQL_ENDPOINT, SPARQL_TIMEOUT, CONTEXT_DIR
from ..utils.owlready2_adapter import adapt_sparql_for_owlready2, format_owlready2_results
from ..utils.query_cache import QueryCache
from .sparql_builder import SPARQLQueryBuilder

# Initialize cache for learning
cache = QueryCache(CONTEXT_DIR)


class SPARQLQueryParams(BaseModel):
    """Parameters for SPARQL query execution."""
    query: str = Field(..., description="SPARQL query to execute")
    parameters: Optional[List[str]] = Field(None, description="Query parameters")
    timeout: int = Field(SPARQL_TIMEOUT, description="Query timeout in milliseconds")
    adapt_for_owlready2: bool = Field(True, description="Adapt query for Owlready2 compatibility")


class ProgressiveQueryParams(BaseModel):
    """Parameters for progressive query building."""
    base_pattern: str = Field(..., description="Base SPARQL pattern")
    filters: Optional[List[str]] = Field(None, description="Filter conditions")
    aggregations: Optional[Dict[str, str]] = Field(None, description="Aggregation functions")
    group_by: Optional[List[str]] = Field(None, description="Group by variables")


async def execute_sparql_query(
    query: str,
    parameters: Optional[List[str]] = None,
    timeout: int = SPARQL_TIMEOUT,
    adapt_for_owlready2: bool = True,
    purpose: str = None,
    analysis_type: str = None
) -> Dict[str, Any]:
    """
    Execute SPARQL query against the MES ontology with learning.
    
    Args:
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
        # Check cache for similar query
        if purpose:
            similar = cache.find_similar_success(purpose, analysis_type)
            if similar:
                print(f"Found similar query pattern: {similar['pattern']}")
        
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
                    
                    # Add to cache
                    if purpose and formatted_results:
                        cache.add_success(
                            query=adapted_query,
                            purpose=purpose,
                            results=formatted_results,
                            row_count=len(formatted_results),
                            analysis_type=analysis_type
                        )
                    
                    return {
                        "success": True,
                        "results": formatted_results,
                        "query": adapted_query,
                        "row_count": len(formatted_results),
                        "cached": False
                    }
                else:
                    error_text = await response.text()
                    
                    # Record failure
                    cache.add_failure(query, error_text)
                    
                    # Attempt common fixes
                    if "Unknown prefix" in error_text:
                        fixed_query = query.replace("mes:", "mes_ontology_populated:")
                        return await execute_sparql_query(
                            fixed_query, parameters, timeout, 
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
# FunctionTool automatically extracts metadata from the function's docstring and annotations
sparql_tool = FunctionTool(execute_sparql_query)

# Initialize query builder
query_builder = SPARQLQueryBuilder()


# Discovery queries for ontology exploration
async def discover_classes() -> Dict[str, Any]:
    """Discover all classes in the ontology."""
    query = """SELECT DISTINCT ?class WHERE {
        ?class a owl:Class .
        FILTER(ISIRI(?class))
    }
    ORDER BY ?class"""
    return await execute_sparql_query(query)


async def discover_equipment_instances() -> Dict[str, Any]:
    """Discover all equipment instances in the ontology."""
    query = """SELECT DISTINCT ?equipment ?type WHERE {
        ?equipment a ?type .
        ?type rdfs:subClassOf* mes_ontology_populated:Equipment .
        FILTER(ISIRI(?equipment))
        FILTER(ISIRI(?type))
    }
    ORDER BY ?equipment"""
    result = await execute_sparql_query(query)
    
    # Equipment discovery tracked in cache via purpose
    if result.get('success') and result.get('results'):
        cache.add_success(
            query=query,
            purpose="Discovered equipment instances",
            results=result.get('results'),
            row_count=len(result.get('results')),
            analysis_type="discovery"
        )
    
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


# New functions using the query builder
async def query_downtime_pareto() -> Dict[str, Any]:
    """Get Pareto analysis of downtime reasons with proper aggregation."""
    query = query_builder.build_downtime_pareto_query()
    return await execute_sparql_query(query)


async def query_time_series_downtime(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """Get time series of downtime events with optional date filtering."""
    query = query_builder.build_time_series_query(start_date, end_date)
    return await execute_sparql_query(query)


async def query_oee_analysis(equipment_type: Optional[str] = None) -> Dict[str, Any]:
    """Analyze OEE metrics by equipment with aggregation."""
    query = query_builder.build_oee_analysis_query(equipment_type)
    return await execute_sparql_query(query)


async def query_defect_analysis() -> Dict[str, Any]:
    """Analyze defect rates by product and line."""
    query = query_builder.build_defect_analysis_query()
    return await execute_sparql_query(query)


async def build_progressive_query(
    params: ProgressiveQueryParams
) -> Dict[str, Any]:
    """Build and execute a query progressively with optional components."""
    query = query_builder.build_progressive_query(
        params.base_pattern, params.filters, params.aggregations, params.group_by
    )
    return await execute_sparql_query(query)