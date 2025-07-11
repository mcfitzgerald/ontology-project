"""
SPARQL query execution service using Owlready2
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from functools import lru_cache
import json

from owlready2 import get_ontology, default_world, World
import owlready2.sparql

from .config import settings
from .utils import Timer, format_query_results, truncate_results


logger = logging.getLogger(__name__)


class SPARQLService:
    """Service for executing SPARQL queries against the ontology"""
    
    def __init__(self, ontology_path: str, thread_pool_size: int = 4):
        """
        Initialize the SPARQL service.
        
        Args:
            ontology_path: Path to the OWL ontology file
            thread_pool_size: Size of thread pool for query execution
        """
        self.ontology_path = ontology_path
        self.thread_pool_size = thread_pool_size
        self.world: Optional[World] = None
        self.ontology = None
        self.executor: Optional[ThreadPoolExecutor] = None
        self.loaded_at: Optional[datetime] = None
        self._ontology_metadata: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize the service and load the ontology"""
        async with self._lock:
            if self.world is not None:
                logger.info("SPARQL service already initialized")
                return
            
            logger.info(f"Initializing SPARQL service with ontology: {self.ontology_path}")
            
            # Create thread pool executor
            self.executor = ThreadPoolExecutor(
                max_workers=self.thread_pool_size,
                thread_name_prefix="sparql-"
            )
            
            # Load ontology in thread pool
            try:
                await self._load_ontology()
                logger.info("SPARQL service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize SPARQL service: {e}")
                if self.executor:
                    self.executor.shutdown(wait=False)
                    self.executor = None
                raise
    
    async def _load_ontology(self):
        """Load the ontology in a thread"""
        loop = asyncio.get_event_loop()
        
        def _load():
            # Create a new world for thread safety
            self.world = World()
            
            # Load the ontology
            self.ontology = get_ontology(
                f"file://{self.ontology_path}"
            ).load(world=self.world)
            
            # Extract metadata
            self._extract_metadata()
            self.loaded_at = datetime.utcnow()
            
            return True
        
        await loop.run_in_executor(self.executor, _load)
    
    def _extract_metadata(self):
        """Extract metadata from the loaded ontology"""
        try:
            # Get ontology IRI and basic info
            self._ontology_metadata["iri"] = str(self.ontology.base_iri)
            self._ontology_metadata["name"] = getattr(self.ontology, "name", "MES Factory Ontology")
            
            # Try to get version from ontology
            # First check for standard version property
            version_props = list(self.world.sparql("""
                SELECT ?version WHERE {
                    ?ont a owl:Ontology .
                    ?ont owl:versionInfo ?version .
                }
            """))
            
            if version_props:
                self._ontology_metadata["version"] = str(version_props[0][0])
            else:
                # Fall back to config version
                self._ontology_metadata["version"] = settings.api_version
            
            # Get entity counts
            with self.ontology:
                equipment_count = len(list(self.ontology.Equipment.instances()))
                product_count = len(list(self.ontology.Product.instances()))
                order_count = len(list(self.ontology.ProductionOrder.instances()))
                event_count = len(list(self.ontology.Event.instances()))
                production_log_count = len(list(self.ontology.ProductionLog.instances()))
                downtime_log_count = len(list(self.ontology.DowntimeLog.instances()))
            
            self._ontology_metadata["statistics"] = {
                "equipment": equipment_count,
                "products": product_count,
                "production_orders": order_count,
                "total_events": event_count,
                "production_logs": production_log_count,
                "downtime_logs": downtime_log_count
            }
            
        except Exception as e:
            logger.warning(f"Failed to extract some metadata: {e}")
            # Ensure we have basic metadata
            if "version" not in self._ontology_metadata:
                self._ontology_metadata["version"] = "unknown"
            if "statistics" not in self._ontology_metadata:
                self._ontology_metadata["statistics"] = {}
    
    async def execute_query(
        self,
        query: str,
        parameters: Optional[List[Any]] = None,
        timeout: Optional[int] = None
    ) -> Tuple[List[List[Any]], List[str], Dict[str, Any]]:
        """
        Execute a SPARQL query asynchronously.
        
        Args:
            query: SPARQL query string
            parameters: Optional query parameters
            timeout: Query timeout in seconds
            
        Returns:
            Tuple of (results, column_names, execution_metadata)
        """
        if not self.world:
            raise RuntimeError("SPARQL service not initialized")
        
        timeout = timeout or settings.query_timeout_seconds
        loop = asyncio.get_event_loop()
        
        # Execute query in thread pool
        try:
            with Timer() as timer:
                future = loop.run_in_executor(
                    self.executor,
                    self._execute_query_sync,
                    query,
                    parameters
                )
                
                # Wait with timeout
                results, columns = await asyncio.wait_for(
                    future,
                    timeout=timeout
                )
            
            # Format results
            formatted_results, formatted_columns = format_query_results(results, columns)
            
            # Truncate if needed
            truncated_results, was_truncated = truncate_results(
                formatted_results,
                settings.max_result_rows
            )
            
            metadata = {
                "query_time_ms": timer.elapsed_ms,
                "prepared_query": parameters is not None,
                "truncated": was_truncated
            }
            
            return truncated_results, formatted_columns, metadata
            
        except asyncio.TimeoutError:
            raise TimeoutError(f"Query exceeded timeout of {timeout} seconds")
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def _execute_query_sync(
        self,
        query: str,
        parameters: Optional[List[Any]] = None
    ) -> Tuple[List[List[Any]], List[str]]:
        """
        Execute SPARQL query synchronously (runs in thread pool).
        
        Args:
            query: SPARQL query string
            parameters: Optional query parameters
            
        Returns:
            Tuple of (results, column_names)
        """
        # Prepare the query
        prepared_query = self.world.prepare_sparql(query)
        
        # Get column names
        column_names = getattr(prepared_query, 'column_names', [])
        
        # Execute query
        if parameters:
            results = list(prepared_query.execute(parameters))
        else:
            results = list(prepared_query.execute())
        
        return results, column_names
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the SPARQL service"""
        status = {
            "ontology_loaded": self.world is not None,
            "thread_pool_active": self.executor is not None,
            "ontology_stats": None,
            "loaded_at": self.loaded_at.isoformat() if self.loaded_at else None
        }
        
        if self.world:
            # Try a simple query to verify it's working
            try:
                loop = asyncio.get_event_loop()
                test_result = await loop.run_in_executor(
                    self.executor,
                    lambda: list(self.world.sparql("SELECT (COUNT(*) as ?count) WHERE { ?s ?p ?o } LIMIT 1"))
                )
                status["query_test_passed"] = len(test_result) > 0
                status["ontology_stats"] = self._ontology_metadata.get("statistics", {})
            except Exception as e:
                logger.error(f"Health check query failed: {e}")
                status["query_test_passed"] = False
                status["error"] = str(e)
        
        return status
    
    def get_ontology_info(self) -> Dict[str, Any]:
        """Get information about the loaded ontology"""
        if not self.world:
            raise RuntimeError("Ontology not loaded")
        
        return {
            "iri": self._ontology_metadata.get("iri", ""),
            "name": self._ontology_metadata.get("name", ""),
            "version": self._ontology_metadata.get("version", ""),
            "statistics": self._ontology_metadata.get("statistics", {}),
            "loaded_at": self.loaded_at
        }
    
    @lru_cache(maxsize=32)
    def prepare_query(self, query: str):
        """
        Prepare a SPARQL query for repeated execution.
        
        Args:
            query: SPARQL query string
            
        Returns:
            Prepared query object
        """
        if not self.world:
            raise RuntimeError("SPARQL service not initialized")
        
        return self.world.prepare_sparql(query)
    
    async def shutdown(self):
        """Shutdown the SPARQL service"""
        logger.info("Shutting down SPARQL service")
        
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None
        
        self.world = None
        self.ontology = None
        self.loaded_at = None
        self._ontology_metadata.clear()


# Global service instance
sparql_service = SPARQLService(
    ontology_path=str(settings.ontology_path),
    thread_pool_size=settings.thread_pool_size
)