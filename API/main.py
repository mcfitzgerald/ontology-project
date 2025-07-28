"""
FastAPI application for SPARQL query execution against MES ontology
"""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .models import (
    SPARQLQueryRequest,
    SPARQLQueryResponse,
    QueryResultData,
    QueryMetadata,
    ErrorResponse,
    ErrorDetail,
    HealthCheckResponse,
    HealthStatus,
    OntologyInfo,
    ExampleQuery,
    ExampleQueriesResponse
)
from .sparql_service import sparql_service
from .utils import (
    detect_query_type,
    quick_sparql_check,
    sanitize_query,
    get_error_hint
)


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting MES Ontology SPARQL API")
    try:
        await sparql_service.initialize()
        logger.info("SPARQL service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize SPARQL service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down MES Ontology SPARQL API")
    await sparql_service.shutdown()


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS if enabled
if settings.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                type="http_error",
                message=exc.detail,
                hint=None
            ),
            request_id=str(uuid.uuid4())
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(
                type="internal_error",
                message="An internal server error occurred",
                hint="Please check your query and try again"
            ),
            request_id=str(uuid.uuid4())
        ).model_dump()
    )


# Routes
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Check API and ontology health status"""
    try:
        health_status = await sparql_service.get_health_status()
        
        # Determine overall status
        if not health_status["ontology_loaded"]:
            status = HealthStatus.UNHEALTHY
            message = "Ontology not loaded"
        elif not health_status.get("query_test_passed", False):
            status = HealthStatus.DEGRADED
            message = "Ontology loaded but query test failed"
        else:
            status = HealthStatus.HEALTHY
            message = "All systems operational"
        
        return HealthCheckResponse(
            status=status,
            ontology_loaded=health_status["ontology_loaded"],
            thread_pool_active=health_status["thread_pool_active"],
            ontology_stats=health_status.get("ontology_stats"),
            message=message
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status=HealthStatus.UNHEALTHY,
            ontology_loaded=False,
            thread_pool_active=False,
            message=f"Health check failed: {str(e)}"
        )


@app.post("/sparql/query", response_model=SPARQLQueryResponse)
async def execute_sparql_query(request: SPARQLQueryRequest):
    """Execute a SPARQL query against the ontology"""
    try:
        # Sanitize query
        query = sanitize_query(request.query)
        
        # Quick validation
        warning = quick_sparql_check(query, settings.max_query_length)
        if warning and "not supported" in warning:
            # This is an error, not just a warning
            raise HTTPException(
                status_code=400,
                detail=warning
            )
        
        # Detect query type
        query_type = detect_query_type(query)
        
        # Execute query
        try:
            results, columns, metadata = await sparql_service.execute_query(
                query=query,
                parameters=request.parameters,
                timeout=request.timeout,
                use_names=request.use_names
            )
        except TimeoutError as e:
            raise HTTPException(
                status_code=408,
                detail=f"Query timeout: {str(e)}. Try simplifying your query or increasing the timeout"
            )
        except Exception as e:
            error_msg = str(e)
            hint = get_error_hint(error_msg)
            
            # Determine suggested pattern based on error type
            suggested_pattern = None
            if "count" in error_msg.lower() and "group by" in error_msg.lower():
                suggested_pattern = "Get downtime events with reasons"
            elif "equipment" in error_msg.lower():
                suggested_pattern = "Get all equipment"
            
            # Build error detail
            error_detail = ErrorDetail(
                type="sparql_error",
                message=error_msg,
                hint=hint,
                suggested_pattern=suggested_pattern,
                documentation_link="/Context/owlready2_sparql_lean_reference.md" if hint else None
            )
            
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error=error_detail,
                    request_id=str(uuid.uuid4())
                ).model_dump()
            )
        
        # Get ontology info
        ontology_info = sparql_service.get_ontology_info()
        
        # Build response
        response = SPARQLQueryResponse(
            data=QueryResultData(
                columns=columns,
                results=results,
                row_count=len(results),
                truncated=metadata.get("truncated", False)
            ),
            metadata=QueryMetadata(
                query_time_ms=metadata["query_time_ms"],
                query_type=query_type,
                ontology_version=ontology_info["version"],
                prepared_query=metadata["prepared_query"]
            ),
            warning=warning
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Query execution failed: {e}", exc_info=True)
        raise


@app.get("/ontology/info", response_model=OntologyInfo)
async def get_ontology_info():
    """Get information about the loaded ontology"""
    try:
        info = sparql_service.get_ontology_info()
        return OntologyInfo(**info)
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {str(e)}. The ontology may still be loading"
        )


@app.get("/sparql/examples", response_model=ExampleQueriesResponse)
async def get_example_queries():
    """Get example SPARQL queries for the MES ontology"""
    examples = [
        ExampleQuery(
            name="List All Equipment",
            description="Get all equipment instances in the factory",
            query="""SELECT ?equipment ?type WHERE {
    ?equipment a ?type .
    ?type rdfs:subClassOf* owl:Thing .
    FILTER(ISIRI(?equipment))
} LIMIT 20"""
        ),
        ExampleQuery(
            name="Count Entity Types",
            description="Count different types of entities in the ontology",
            query="""SELECT ?type (COUNT(?x) AS ?count) WHERE {
    ?x a ?type .
    FILTER(ISIRI(?type))
} GROUP BY ?type
ORDER BY DESC(?count)
LIMIT 10"""
        ),
        ExampleQuery(
            name="Get Entity Properties",
            description="Get all properties for a specific entity",
            query="""SELECT ?prop ?value WHERE {
    ?? ?prop ?value .
    FILTER(ISIRI(?prop))
} LIMIT 30""",
            parameters=["http://mes-ontology.org/factory.owl#LINE1-FIL"]
        ),
        ExampleQuery(
            name="Get All Classes",
            description="List all classes defined in the ontology",
            query="""SELECT DISTINCT ?class WHERE {
    ?x a ?class .
    ?class a owl:Class .
} LIMIT 20"""
        ),
        ExampleQuery(
            name="Get Relationships",
            description="Find all relationships between entities",
            query="""SELECT ?s ?p ?o WHERE {
    ?s ?p ?o .
    FILTER(ISIRI(?s) && ISIRI(?p) && ISIRI(?o))
} LIMIT 50"""
        ),
        ExampleQuery(
            name="Get Datatype Properties",
            description="Find all datatype property values",
            query="""SELECT ?s ?p ?o WHERE {
    ?s ?p ?o .
    FILTER(ISIRI(?s))
    FILTER(ISIRI(?p))
    FILTER(!ISIRI(?o))
} LIMIT 50"""
        ),
        ExampleQuery(
            name="Simple Test Query",
            description="Basic query to test SPARQL endpoint",
            query="""SELECT ?x WHERE {
    ?x a owl:Thing .
} LIMIT 5"""
        )
    ]
    
    return ExampleQueriesResponse(examples=examples)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "endpoints": {
            "health": "/health",
            "execute_query": "/sparql/query",
            "ontology_info": "/ontology/info",
            "examples": "/sparql/examples",
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )