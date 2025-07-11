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
    lifespan=lifespan
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
                detail=ErrorResponse(
                    error=ErrorDetail(
                        type="unsupported_query",
                        message=warning,
                        hint="Check Owlready2 documentation for supported SPARQL features"
                    )
                ).model_dump()
            )
        
        # Detect query type
        query_type = detect_query_type(query)
        
        # Execute query
        try:
            results, columns, metadata = await sparql_service.execute_query(
                query=query,
                parameters=request.parameters,
                timeout=request.timeout
            )
        except TimeoutError as e:
            raise HTTPException(
                status_code=408,
                detail=ErrorResponse(
                    error=ErrorDetail(
                        type="timeout",
                        message=str(e),
                        hint="Try simplifying your query or increasing the timeout"
                    )
                ).model_dump()
            )
        except Exception as e:
            error_msg = str(e)
            hint = get_error_hint(error_msg)
            
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error=ErrorDetail(
                        type="invalid_sparql",
                        message=error_msg,
                        hint=hint
                    )
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
            detail=ErrorResponse(
                error=ErrorDetail(
                    type="service_unavailable",
                    message=str(e),
                    hint="The ontology may still be loading"
                )
            ).model_dump()
        )


@app.get("/sparql/examples", response_model=ExampleQueriesResponse)
async def get_example_queries():
    """Get example SPARQL queries for the MES ontology"""
    examples = [
        ExampleQuery(
            name="Current OEE by Equipment",
            description="Get the most recent OEE score for each equipment",
            query="""
                SELECT ?equipment ?oee ?timestamp WHERE {
                    ?equipment a :Equipment .
                    ?equipment :logsEvent ?event .
                    ?event :hasOEEScore ?oee .
                    ?event :hasTimestamp ?timestamp .
                } ORDER BY DESC(?timestamp) LIMIT 100
            """
        ),
        ExampleQuery(
            name="Equipment Downtime Summary",
            description="Find equipment with downtime events and their reasons",
            query="""
                SELECT ?equipment ?reason ?timestamp WHERE {
                    ?equipment a :Equipment .
                    ?equipment :logsEvent ?event .
                    ?event a :DowntimeLog .
                    ?event :hasDowntimeReasonCode ?reason .
                    ?event :hasTimestamp ?timestamp .
                } ORDER BY DESC(?timestamp) LIMIT 50
            """
        ),
        ExampleQuery(
            name="Production by Product",
            description="Sum good units produced by product",
            query="""
                SELECT ?product (SUM(?units) as ?total_units) WHERE {
                    ?order :producesProduct ?product .
                    ?equipment :executesOrder ?order .
                    ?equipment :logsEvent ?event .
                    ?event a :ProductionLog .
                    ?event :hasGoodUnits ?units .
                } GROUP BY ?product
            """
        ),
        ExampleQuery(
            name="Low Performance Equipment",
            description="Find equipment with performance score below 90%",
            query="""
                SELECT DISTINCT ?equipment ?performance WHERE {
                    ?equipment a :Equipment .
                    ?equipment :logsEvent ?event .
                    ?event :hasPerformanceScore ?performance .
                    FILTER(?performance < 90.0)
                } LIMIT 20
            """
        ),
        ExampleQuery(
            name="Equipment Hierarchy",
            description="Show equipment and their production line relationships",
            query="""
                SELECT ?equipment ?line ?upstream WHERE {
                    ?equipment a :Equipment .
                    ?equipment :belongsToLine ?line .
                    OPTIONAL { ?equipment :isUpstreamOf ?upstream }
                }
            """
        ),
        ExampleQuery(
            name="Quality Issues",
            description="Find events with high scrap rates",
            query="""
                SELECT ?equipment ?product ?scrap ?good ?quality WHERE {
                    ?equipment :logsEvent ?event .
                    ?event a :ProductionLog .
                    ?event :hasScrapUnits ?scrap .
                    ?event :hasGoodUnits ?good .
                    ?event :hasQualityScore ?quality .
                    ?equipment :executesOrder ?order .
                    ?order :producesProduct ?product .
                    FILTER(?quality < 98.0)
                } ORDER BY ?quality LIMIT 50
            """
        ),
        ExampleQuery(
            name="Parametrized Query Example",
            description="Find events for specific equipment (using parameters)",
            query="""
                SELECT ?timestamp ?status ?oee WHERE {
                    ?? :logsEvent ?event .
                    ?event :hasTimestamp ?timestamp .
                    ?event :hasMachineStatus ?status .
                    ?event :hasOEEScore ?oee .
                } ORDER BY DESC(?timestamp) LIMIT 20
            """,
            parameters=["LINE1-FIL"]
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
            "examples": "/sparql/examples"
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