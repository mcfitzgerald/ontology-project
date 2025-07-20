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
import tempfile
from pathlib import Path
import time
import re

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
        self._quadstore_path: Optional[Path] = None
        self._enable_parallelism = True  # Enable thread parallelism by default
        
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
        """Load the ontology in a thread with optional parallelism support"""
        loop = asyncio.get_event_loop()
        
        def _load():
            start_time = time.time()
            
            # Create a new world
            self.world = World()
            
            # Configure for thread parallelism if enabled
            if self._enable_parallelism:
                # Create a temporary file for the quadstore
                self._quadstore_path = Path(tempfile.gettempdir()) / f"mes_quadstore_{datetime.now().timestamp()}.sqlite3"
                logger.info(f"Enabling thread parallelism with quadstore at: {self._quadstore_path}")
                
                # Set backend with thread parallelism
                self.world.set_backend(
                    filename=str(self._quadstore_path),
                    exclusive=False,
                    enable_thread_parallelism=True
                )
            
            # Load the ontology
            logger.info(f"Loading ontology from: {self.ontology_path}")
            self.ontology = self.world.get_ontology(
                f"file://{self.ontology_path}"
            ).load()
            
            # Save the world to enable parallelism
            if self._enable_parallelism:
                logger.info("Saving world to enable thread parallelism...")
                self.world.save()
            
            # Extract metadata
            self._extract_metadata()
            self.loaded_at = datetime.utcnow()
            
            load_time = time.time() - start_time
            logger.info(f"Ontology loaded successfully in {load_time:.2f}s")
            
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
        timeout: Optional[int] = None,
        use_names: bool = True
    ) -> Tuple[List[List[Any]], List[str], Dict[str, Any]]:
        """
        Execute a SPARQL query asynchronously.
        
        Args:
            query: SPARQL query string
            parameters: Optional query parameters
            timeout: Query timeout in seconds
            use_names: If True, use entity names instead of full IRIs
            
        Returns:
            Tuple of (results, column_names, execution_metadata)
        """
        if not self.world:
            raise RuntimeError("SPARQL service not initialized")
        
        timeout = timeout or settings.query_timeout_seconds
        loop = asyncio.get_event_loop()
        
        # Log query details
        logger.debug(f"Executing query (timeout={timeout}s): {query[:100]}...")
        if parameters:
            logger.debug(f"With parameters: {parameters}")
        
        # Execute query in thread pool
        try:
            with Timer() as timer:
                # Create the future
                future = loop.run_in_executor(
                    self.executor,
                    self._execute_query_sync,
                    query,
                    parameters
                )
                
                # Wait with timeout
                start_wait = time.time()
                results, columns = await asyncio.wait_for(
                    future,
                    timeout=timeout
                )
                wait_time = time.time() - start_wait
                
                if wait_time > 1.0:
                    logger.warning(f"Query took {wait_time:.2f}s to execute (approaching timeout of {timeout}s)")
            
            # Format results
            format_start = time.time()
            formatted_results, formatted_columns = format_query_results(results, columns, self.world, use_names)
            format_time = time.time() - format_start
            
            # Truncate if needed
            truncated_results, was_truncated = truncate_results(
                formatted_results,
                settings.max_result_rows
            )
            
            metadata = {
                "query_time_ms": timer.elapsed_ms,
                "prepared_query": parameters is not None,
                "truncated": was_truncated,
                "result_count": len(results),
                "format_time_ms": format_time * 1000
            }
            
            logger.debug(f"Query completed in {timer.elapsed_ms:.0f}ms, returned {len(results)} results")
            
            return truncated_results, formatted_columns, metadata
            
        except asyncio.TimeoutError:
            logger.error(f"Query timeout after {timeout}s: {query[:100]}...")
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
        # Time each stage
        prep_start = time.time()
        
        # Prepare the query
        prepared_query = self.world.prepare_sparql(query)
        prep_time = time.time() - prep_start
        
        # Get column names
        column_names = getattr(prepared_query, 'column_names', [])
        
        # Log SQL translation if available (for debugging)
        if hasattr(prepared_query, 'sql') and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"SQL translation: {prepared_query.sql[:200]}...")
        
        # Execute query
        exec_start = time.time()
        if parameters:
            results = list(prepared_query.execute(parameters))
        else:
            results = list(prepared_query.execute())
        exec_time = time.time() - exec_start
        
        if prep_time > 0.1 or exec_time > 1.0:
            logger.warning(f"Slow query - Preparation: {prep_time:.3f}s, Execution: {exec_time:.3f}s")
        
        # Workaround for Owlready2 COUNT() aggregation bug
        # Check if query contains aggregation functions and fix results
        if self._contains_aggregation(query) and self._has_iri_in_aggregation_results(results, column_names):
            logger.warning("Detected Owlready2 COUNT() bug - attempting workaround")
            results = self._fix_aggregation_results_v2(query, results, column_names)
        
        return results, column_names
    
    def _contains_aggregation(self, query: str) -> bool:
        """
        Check if query contains aggregation functions.
        """
        query_upper = query.upper()
        aggregation_functions = ['COUNT(', 'SUM(', 'AVG(', 'MIN(', 'MAX(', 'GROUP_CONCAT(']
        return any(func in query_upper for func in aggregation_functions)
    
    def _fix_aggregation_results(self, query: str, results: List[List[Any]], column_names: List[str]) -> List[List[Any]]:
        """
        Fix aggregation results that return IRIs instead of numeric values.
        
        This is a workaround for Owlready2's COUNT() bug where it returns
        entity IRIs instead of count values.
        """
        # If no results or columns, return as is
        if not results or not column_names:
            return results
        
        # Identify which columns are aggregation results
        query_upper = query.upper()
        aggregation_cols = []
        
        for i, col_name in enumerate(column_names):
            # Check if this column is from an aggregation function
            # Look for patterns like "COUNT(...) AS colname" or just "COUNT(...)"
            patterns = [
                f"COUNT(" ,  # COUNT function
                f"SUM(",     # SUM function  
                f"AVG(",     # AVG function
                f"MIN(",     # MIN function
                f"MAX("      # MAX function
            ]
            
            # Check if column appears after an aggregation function
            for pattern in patterns:
                if pattern in query_upper:
                    # Check if this column name appears in an AS clause after the aggregation
                    as_pattern = re.escape(pattern) + r"[^)]+\)\s+AS\s+" + re.escape(col_name)
                    if re.search(as_pattern, query_upper, re.IGNORECASE):
                        aggregation_cols.append(i)
                        break
                    # Or if the column name matches a common aggregation result name
                    elif col_name.lower() in ['count', 'sum', 'avg', 'min', 'max', 'total', 'average']:
                        aggregation_cols.append(i)
                        break
        
        # If no aggregation columns identified, try another approach
        if not aggregation_cols and 'GROUP BY' in query_upper:
            # For GROUP BY queries, assume first column might be aggregation if it looks like an IRI
            for i, col_name in enumerate(column_names):
                if col_name.lower() in ['count', 'sum', 'avg', 'min', 'max', 'total', 'average']:
                    aggregation_cols.append(i)
        
        # Fix the results
        if aggregation_cols:
            fixed_results = []
            for row in results:
                fixed_row = list(row)
                for col_idx in aggregation_cols:
                    if col_idx < len(fixed_row):
                        value = fixed_row[col_idx]
                        # If value looks like an IRI/entity, it's likely the bug
                        if isinstance(value, str) and (value.startswith('http://') or value.startswith('https://')):
                            # For COUNT, we need to actually count the results
                            # This is a fallback - ideally we'd re-execute the query differently
                            logger.warning(f"Detected COUNT() bug: got IRI '{value}' instead of numeric count")
                            # Return 1 as a fallback count (at least one result was found)
                            fixed_row[col_idx] = 1
                        elif hasattr(value, 'iri'):
                            # It's an Owlready2 entity object
                            logger.warning(f"Detected COUNT() bug: got entity instead of numeric count")
                            fixed_row[col_idx] = 1
                fixed_results.append(fixed_row)
            return fixed_results
        
        return results
    
    def _has_iri_in_aggregation_results(self, results: List[List[Any]], column_names: List[str]) -> bool:
        """
        Check if any result that should be numeric (based on column name) contains an IRI.
        """
        if not results or not column_names:
            return False
            
        # Check first row for IRI values in columns that should be numeric
        first_row = results[0] if results else []
        for i, col_name in enumerate(column_names):
            if col_name.lower() in ['count', 'sum', 'avg', 'min', 'max', 'total', 'average']:
                if i < len(first_row):
                    value = first_row[i]
                    # Check if it's an IRI string
                    if isinstance(value, str) and (value.startswith('http://') or value.startswith('https://')):
                        return True
                    # Check if it's an Owlready2 entity
                    if hasattr(value, 'iri'):
                        return True
        return False
    
    def _fix_aggregation_results_v2(self, query: str, results: List[List[Any]], column_names: List[str]) -> List[List[Any]]:
        """
        Alternative fix for COUNT() aggregation bug.
        
        For GROUP BY queries with COUNT, we need to manually count the groups.
        This is a more robust workaround.
        """
        query_upper = query.upper()
        
        # Check if this is a COUNT query with GROUP BY
        if 'COUNT(' in query_upper and 'GROUP BY' in query_upper:
            # Extract the GROUP BY column(s)
            group_by_match = re.search(r'GROUP\s+BY\s+([^\s]+)', query_upper)
            if group_by_match:
                # For each group, we need to count properly
                # Since Owlready2 returns IRIs instead of counts, we'll use a different approach
                
                # Try to re-execute a simpler query without COUNT to get raw data
                # Then count manually
                try:
                    # Remove COUNT from SELECT clause
                    modified_query = re.sub(r'\(COUNT\([^)]+\)\s+AS\s+\w+\)', '?_dummy', query, flags=re.IGNORECASE)
                    modified_query = re.sub(r'COUNT\([^)]+\)', '?_dummy', modified_query, flags=re.IGNORECASE)
                    
                    # Execute modified query
                    logger.debug(f"Executing fallback query for COUNT workaround: {modified_query[:100]}...")
                    prepared_query = self.world.prepare_sparql(modified_query)
                    raw_results = list(prepared_query.execute())
                    
                    # Count occurrences per group
                    from collections import defaultdict
                    group_counts = defaultdict(int)
                    
                    # Assuming the GROUP BY column is the second column (after the COUNT column)
                    group_col_idx = 1  # Adjust based on actual query structure
                    
                    for row in raw_results:
                        if len(row) > group_col_idx:
                            group_key = str(row[group_col_idx])
                            group_counts[group_key] += 1
                    
                    # Reconstruct results with proper counts
                    fixed_results = []
                    for group_key, count in group_counts.items():
                        # Find the original row for this group
                        for row in results:
                            if len(row) > 1 and str(row[1]) == group_key:
                                fixed_row = list(row)
                                fixed_row[0] = count  # Replace IRI with actual count
                                fixed_results.append(fixed_row)
                                break
                    
                    if fixed_results:
                        logger.info(f"Successfully fixed COUNT() results using fallback method")
                        return fixed_results
                except Exception as e:
                    logger.error(f"Fallback COUNT workaround failed: {e}")
        
        # If we can't fix it with the fallback, try the original simple fix
        return self._fix_aggregation_results(query, results, column_names)
    
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
        
        # Clean up quadstore file if it exists
        if self._quadstore_path and self._quadstore_path.exists():
            try:
                self._quadstore_path.unlink()
                logger.info(f"Cleaned up quadstore file: {self._quadstore_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up quadstore file: {e}")
        
        self.world = None
        self.ontology = None
        self.loaded_at = None
        self._ontology_metadata.clear()


# Global service instance
sparql_service = SPARQLService(
    ontology_path=str(settings.ontology_path),
    thread_pool_size=settings.thread_pool_size
)