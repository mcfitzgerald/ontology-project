"""
Pydantic models for API request/response validation
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class QueryType(str, Enum):
    """Supported SPARQL query types"""
    SELECT = "select"
    INSERT = "insert"
    DELETE = "delete"
    UNKNOWN = "unknown"


class SPARQLQueryRequest(BaseModel):
    """Request model for SPARQL query execution"""
    
    query: str = Field(
        ...,
        description="SPARQL query to execute",
        min_length=1,
        example="SELECT ?equipment ?oee WHERE { ?equipment :hasOEEScore ?oee } LIMIT 10"
    )
    
    parameters: Optional[List[Any]] = Field(
        default=None,
        description="Query parameters for prepared statements (using ?? placeholders)"
    )
    
    timeout: Optional[int] = Field(
        default=None,
        description="Query timeout in seconds (overrides default)",
        ge=1,
        le=300
    )
    
    use_names: bool = Field(
        default=True,
        description="Return entity names instead of full IRIs (e.g., 'LINE1' instead of 'http://mes-ontology.org/factory.owl#LINE1')"
    )
    
    @field_validator('query')
    @classmethod
    def validate_query_not_empty(cls, v: str) -> str:
        """Ensure query is not just whitespace"""
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v


class QueryResultData(BaseModel):
    """Query result data with metadata for DataFrame construction"""
    
    columns: List[str] = Field(
        ...,
        description="Column names from the query (e.g., ['?equipment', '?oee'])"
    )
    
    results: List[List[Any]] = Field(
        ...,
        description="Query results as list of rows"
    )
    
    row_count: int = Field(
        ...,
        description="Number of rows returned"
    )
    
    truncated: bool = Field(
        default=False,
        description="Whether results were truncated due to limits"
    )


class QueryMetadata(BaseModel):
    """Metadata about query execution"""
    
    query_time_ms: int = Field(
        ...,
        description="Query execution time in milliseconds"
    )
    
    query_type: QueryType = Field(
        ...,
        description="Type of SPARQL query executed"
    )
    
    ontology_version: str = Field(
        ...,
        description="Version of the ontology"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of query execution"
    )
    
    prepared_query: bool = Field(
        default=False,
        description="Whether query was executed as prepared statement"
    )


class SPARQLQueryResponse(BaseModel):
    """Successful query response"""
    
    status: str = Field(
        default="success",
        description="Response status"
    )
    
    data: QueryResultData = Field(
        ...,
        description="Query results and column information"
    )
    
    metadata: QueryMetadata = Field(
        ...,
        description="Query execution metadata"
    )
    
    warning: Optional[str] = Field(
        default=None,
        description="Optional warning message"
    )


class ErrorDetail(BaseModel):
    """Detailed error information"""
    
    type: str = Field(
        ...,
        description="Error type (e.g., 'invalid_sparql', 'timeout', 'internal_error')"
    )
    
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    
    hint: Optional[str] = Field(
        default=None,
        description="Helpful hint for resolving the error"
    )
    
    query_position: Optional[int] = Field(
        default=None,
        description="Character position in query where error occurred"
    )
    
    suggested_pattern: Optional[str] = Field(
        default=None,
        description="Reference to a working pattern from query_patterns.json"
    )
    
    documentation_link: Optional[str] = Field(
        default=None,
        description="Link to relevant documentation section"
    )


class ErrorResponse(BaseModel):
    """Error response model"""
    
    status: str = Field(
        default="error",
        description="Response status"
    )
    
    error: ErrorDetail = Field(
        ...,
        description="Error details"
    )
    
    request_id: Optional[str] = Field(
        default=None,
        description="Request ID for debugging"
    )


class HealthStatus(str, Enum):
    """Health check status values"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheckResponse(BaseModel):
    """Health check response"""
    
    status: HealthStatus = Field(
        ...,
        description="Overall health status"
    )
    
    ontology_loaded: bool = Field(
        ...,
        description="Whether ontology is successfully loaded"
    )
    
    thread_pool_active: bool = Field(
        ...,
        description="Whether thread pool is active"
    )
    
    ontology_stats: Optional[Dict[str, int]] = Field(
        default=None,
        description="Basic ontology statistics"
    )
    
    message: Optional[str] = Field(
        default=None,
        description="Additional status message"
    )


class OntologyInfo(BaseModel):
    """Ontology information response"""
    
    iri: str = Field(..., description="Ontology IRI")
    name: str = Field(..., description="Ontology name")
    version: str = Field(..., description="Ontology version")
    statistics: Dict[str, int] = Field(
        ...,
        description="Entity counts (equipment, products, events, etc.)"
    )
    loaded_at: datetime = Field(..., description="When ontology was loaded")


class ExampleQuery(BaseModel):
    """Example SPARQL query"""
    
    name: str = Field(..., description="Query name")
    description: str = Field(..., description="What the query does")
    query: str = Field(..., description="SPARQL query text")
    parameters: Optional[List[Any]] = Field(
        default=None,
        description="Example parameters if applicable"
    )


class ExampleQueriesResponse(BaseModel):
    """Response containing example queries"""
    
    examples: List[ExampleQuery] = Field(
        ...,
        description="List of example SPARQL queries"
    )