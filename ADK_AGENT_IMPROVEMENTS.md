# Implementation Plan for ADK Agent System Improvements

## Executive Summary

Based on analysis of the trace.json file, this document outlines a comprehensive plan to improve the ADK agent system for manufacturing analytics. The improvements focus on fixing SPARQL query generation, implementing intelligent context sharing, and adding performance monitoring.

## Issues Identified

### 1. **SPARQL Query Problems**
- **Timestamp Filtering**: Queries with `FILTER(ISIRI(?timestamp))` return 0 results, indicating timestamps are stored as literals, not IRIs
- **Repetitive Results**: The downtime query returned 1003 identical rows - LINE2/REASON-UNP-JAM repeated hundreds of times
- **No Aggregation**: Basic Pareto analysis query failed to properly group and count results

### 2. **Agent Coordination Issues**
- **Incomplete Handoffs**: Transfer from OntologyExplorer to DataAnalyst was initiated but no DataAnalyst response appears in the trace
- **Redundant Exploration**: Multiple queries checking the same properties (Equipment, DowntimeLog) without caching results
- **Context Loss**: Agents don't seem to share discovered insights effectively

### 3. **Performance Bottlenecks**
- **Large Result Sets**: Returning 1003 duplicate rows instead of aggregated counts
- **No Query Optimization**: Missing DISTINCT, GROUP BY, and proper aggregation
- **Token Waste**: Total token count reached 14,653 for a simple exploration task

### 4. **Data Model Understanding**
- **Property Discovery**: Equipment class has no direct properties - all properties are on subclasses
- **Timestamp Format**: Agents didn't adapt to timestamp being a literal value
- **Missing Validation**: No checks for data consistency before complex queries

## Phase 1: Fix SPARQL Query Generation (Week 1)

### 1.1 Create SPARQL Query Builder Module
**File**: `adk_agents/tools/sparql_builder.py`
```python
from typing import Dict, List, Optional
import re

class SPARQLQueryBuilder:
    """Enhanced SPARQL query builder with Owlready2 compatibility"""
    
    def __init__(self, namespace: str = "mes_ontology_populated"):
        self.namespace = namespace
        
    def build_downtime_pareto_query(self) -> str:
        """Build optimized Pareto analysis query with proper aggregation"""
        return f"""
        SELECT ?downtimeReason (COUNT(DISTINCT ?downtimeLog) AS ?count)
        WHERE {{
            ?downtimeLog a {self.namespace}:DowntimeLog .
            ?downtimeLog {self.namespace}:hasDowntimeReason ?downtimeReason .
            FILTER(ISIRI(?downtimeReason))
        }}
        GROUP BY ?downtimeReason
        ORDER BY DESC(?count)
        LIMIT 20
        """
    
    def build_time_series_query(self, 
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> str:
        """Build time series query treating timestamps as literals"""
        query = f"""
        SELECT ?timestamp ?line ?downtimeReason ?equipment
        WHERE {{
            ?downtimeLog a {self.namespace}:DowntimeLog .
            ?downtimeLog {self.namespace}:hasTimestamp ?timestamp .
            ?downtimeLog {self.namespace}:hasDowntimeReason ?downtimeReason .
            ?equipment {self.namespace}:logsEvent ?downtimeLog .
            ?equipment {self.namespace}:belongsToLine ?line .
            FILTER(ISIRI(?downtimeReason))
            FILTER(ISIRI(?line))
            # Timestamps are literals, not IRIs
        """
        
        if start_date or end_date:
            query += "\n            FILTER("
            if start_date:
                query += f'?timestamp >= "{start_date}"^^xsd:dateTime'
            if start_date and end_date:
                query += " && "
            if end_date:
                query += f'?timestamp <= "{end_date}"^^xsd:dateTime'
            query += ")"
            
        query += """
        }
        ORDER BY ?timestamp
        LIMIT 1000
        """
        return query
```

### 1.2 Update Query Tool
**File**: `adk_agents/tools/sparql_executor.py`
```python
from .sparql_builder import SPARQLQueryBuilder
from .sparql_validator import validate_and_optimize_query

@tool
def execute_sparql_query(query: str, 
                        tool_context: ToolContext,
                        optimize: bool = True) -> Dict:
    """Execute SPARQL query with validation and optimization"""
    
    # Get cached query builder from state
    builder = tool_context.state.get("_sparql_builder")
    if not builder:
        builder = SPARQLQueryBuilder()
        tool_context.state["_sparql_builder"] = builder
    
    # Validate and optimize
    if optimize:
        query = validate_and_optimize_query(query)
    
    # Execute query
    try:
        result = sparql_service.execute_query(query)
        
        # Cache successful query patterns
        if result["row_count"] > 0:
            patterns = tool_context.state.get("working_query_patterns", [])
            patterns.append({
                "query": query,
                "row_count": result["row_count"],
                "purpose": tool_context.state.get("current_analysis_goal", "unknown")
            })
            tool_context.state["working_query_patterns"] = patterns[-10:]  # Keep last 10
        
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "hint": "Check if timestamps need to be treated as literals, not IRIs"
        }
```

## Phase 2: Implement Agent Memory & Context Sharing (Week 2)

### 2.1 Create Shared Context Manager
**File**: `adk_agents/context/shared_context.py`
```python
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class SharedAgentContext:
    """Manages shared context between agents"""
    
    def __init__(self):
        self.discovered_properties: Dict[str, List[str]] = {}
        self.query_results: Dict[str, Any] = {}
        self.data_patterns: Dict[str, Any] = {}
        self.known_issues: List[Dict[str, str]] = []
        
    def cache_property_discovery(self, class_name: str, properties: List[Dict]):
        """Cache discovered properties for a class"""
        self.discovered_properties[class_name] = {
            "properties": properties,
            "discovered_at": datetime.now().isoformat(),
            "data_types": self._extract_data_types(properties)
        }
    
    def get_cached_properties(self, class_name: str) -> Optional[Dict]:
        """Retrieve cached properties for a class"""
        return self.discovered_properties.get(class_name)
    
    def cache_query_result(self, query_hash: str, result: Dict, purpose: str):
        """Cache query results with metadata"""
        self.query_results[query_hash] = {
            "result": result,
            "purpose": purpose,
            "cached_at": datetime.now().isoformat(),
            "row_count": result.get("row_count", 0)
        }
    
    def record_known_issue(self, issue_type: str, details: str, workaround: str):
        """Record known issues and workarounds"""
        self.known_issues.append({
            "type": issue_type,
            "details": details,
            "workaround": workaround,
            "recorded_at": datetime.now().isoformat()
        })
    
    def to_dict(self) -> Dict:
        """Serialize context for state storage"""
        return {
            "discovered_properties": self.discovered_properties,
            "query_results": list(self.query_results.values())[-20:],  # Keep last 20
            "data_patterns": self.data_patterns,
            "known_issues": self.known_issues
        }
    
    @classmethod
    def from_state(cls, state: Dict) -> 'SharedAgentContext':
        """Reconstruct from state"""
        context = cls()
        shared_data = state.get("_shared_context", {})
        context.discovered_properties = shared_data.get("discovered_properties", {})
        context.data_patterns = shared_data.get("data_patterns", {})
        context.known_issues = shared_data.get("known_issues", [])
        return context
```

### 2.2 Update Orchestrator for Context Management
**File**: `adk_agents/agents/orchestrator.py`
```python
from google.adk.agents import LlmAgent
from ..context.shared_context import SharedAgentContext

def create_orchestrator_agent() -> LlmAgent:
    """Create the main orchestrator agent with context management"""
    
    def context_aware_instruction(context: ReadonlyContext) -> str:
        # Load shared context from state
        shared_context = SharedAgentContext.from_state(context.state())
        
        base_instruction = """
        You are the lead manufacturing analyst coordinating an investigation.
        
        You have access to shared context including:
        - Discovered properties: {property_count} classes explored
        - Cached query results: {query_count} successful queries
        - Known issues: {issue_count} documented workarounds
        
        Your role is to:
        1. Check shared context before delegating exploration tasks
        2. Update shared context with new discoveries
        3. Use known workarounds for common issues
        4. Maintain analysis momentum by reusing successful patterns
        """
        
        return base_instruction.format(
            property_count=len(shared_context.discovered_properties),
            query_count=len(shared_context.query_results),
            issue_count=len(shared_context.known_issues)
        )
    
    def on_before_transfer(callback_context: CallbackContext, 
                          target_agent: str) -> None:
        """Prepare context for agent transfer"""
        shared_context = SharedAgentContext.from_state(callback_context.state)
        
        # Add transfer metadata
        callback_context.state["_transfer_context"] = {
            "from_agent": callback_context.agent_name,
            "to_agent": target_agent,
            "shared_context": shared_context.to_dict(),
            "current_goal": callback_context.state.get("current_analysis_goal", "")
        }
    
    return LlmAgent(
        name="ManufacturingAnalystOrchestrator",
        model="gemini-2.0-flash",
        instruction=context_aware_instruction,
        description="Main coordinator with shared context management",
        tools=[transfer_to_agent_with_context],
        callbacks={
            "on_before_transfer": on_before_transfer
        }
    )
```

## Phase 3: Add Query Validation & Optimization (Week 3)

### 3.1 Create Query Validator
**File**: `adk_agents/tools/sparql_validator.py`
```python
import re
from typing import Tuple, List

def validate_and_optimize_query(query: str) -> str:
    """Validate and optimize SPARQL queries for Owlready2"""
    
    # Add DISTINCT to prevent duplicate results
    if "SELECT ?" in query and "DISTINCT" not in query:
        if not any(agg in query for agg in ["COUNT", "SUM", "AVG", "MIN", "MAX"]):
            query = query.replace("SELECT ?", "SELECT DISTINCT ?")
    
    # Add LIMIT for exploration queries
    if "ORDER BY" in query and "LIMIT" not in query:
        query = query.rstrip().rstrip("}") + "\nLIMIT 100\n}"
    
    # Check for missing GROUP BY with aggregations
    if any(f"({agg}" in query for agg in ["COUNT", "SUM", "AVG"]):
        if "GROUP BY" not in query:
            # Extract non-aggregated variables
            select_match = re.search(r"SELECT.*?WHERE", query, re.DOTALL)
            if select_match:
                vars_in_select = re.findall(r"\?(\w+)(?!\s*\))", select_match.group())
                if vars_in_select:
                    query = query.rstrip().rstrip("}") + f"\nGROUP BY ?{' ?'.join(vars_in_select)}\n}}"
    
    return query

def analyze_query_failure(query: str, error: str) -> Dict[str, Any]:
    """Analyze why a query failed and suggest fixes"""
    
    suggestions = []
    
    if "Undefined prefix" in error:
        suggestions.append("Use full prefix 'mes_ontology_populated:' for all properties")
    
    if "FILTER(ISIRI(?timestamp))" in query and "0 results" in error:
        suggestions.append("Remove FILTER(ISIRI(?timestamp)) - timestamps are literals")
        fixed_query = query.replace("FILTER(ISIRI(?timestamp))", "")
        return {"suggestions": suggestions, "fixed_query": fixed_query}
    
    return {"suggestions": suggestions}
```

### 3.2 Create Data Profiling Tool
**File**: `adk_agents/tools/data_profiler.py`
```python
@tool
def profile_property(class_name: str, 
                    property_name: str,
                    tool_context: ToolContext) -> Dict:
    """Profile a property to understand its data characteristics"""
    
    query = f"""
    SELECT 
        (COUNT(DISTINCT ?value) as ?unique_values)
        (COUNT(?value) as ?total_values)
        (DATATYPE(?value) as ?data_type)
        (SAMPLE(?value) as ?example)
        (MIN(?value) as ?min_value)
        (MAX(?value) as ?max_value)
    WHERE {{
        ?instance a mes_ontology_populated:{class_name} .
        ?instance mes_ontology_populated:{property_name} ?value .
    }}
    GROUP BY (DATATYPE(?value))
    """
    
    result = execute_sparql_query(query, tool_context, optimize=False)
    
    if result["success"]:
        # Cache the profile
        shared_context = SharedAgentContext.from_state(tool_context.state)
        shared_context.data_patterns[f"{class_name}.{property_name}"] = {
            "profile": result["results"],
            "profiled_at": datetime.now().isoformat()
        }
        tool_context.state["_shared_context"] = shared_context.to_dict()
    
    return result
```

## Phase 4: Enhance Agent Instructions and Handoffs (Week 4)

### 4.1 Enhanced OntologyExplorer
**File**: `adk_agents/agents/ontology_explorer.py`
```python
def create_ontology_explorer() -> LlmAgent:
    """Create enhanced OntologyExplorer with caching and profiling"""
    
    instruction = """
    You explore the ontology structure with intelligent caching and data profiling.
    
    ALWAYS follow this workflow:
    1. Check shared context for cached discoveries before querying
    2. When discovering new properties, profile their data types
    3. Test with one instance to understand value formats
    4. Document successful query patterns
    5. Record any issues with workarounds
    
    Key behaviors:
    - Use discover_classes first, check cache before re-querying
    - For each property, use profile_property to understand data types
    - Test if timestamps/dates are IRIs or literals
    - Cache all discoveries in shared context
    
    Known issues from shared context:
    {known_issues}
    
    Cached discoveries:
    {cached_classes}
    """
    
    def dynamic_instruction(context: ReadonlyContext) -> str:
        shared = SharedAgentContext.from_state(context.state())
        
        known_issues = "\n".join([
            f"- {issue['type']}: {issue['workaround']}"
            for issue in shared.known_issues[-5:]
        ])
        
        cached_classes = ", ".join(shared.discovered_properties.keys())
        
        return instruction.format(
            known_issues=known_issues or "None yet",
            cached_classes=cached_classes or "None yet"
        )
    
    return LlmAgent(
        name="OntologyExplorer",
        model="gemini-2.0-flash",
        instruction=dynamic_instruction,
        tools=[
            discover_classes,
            discover_properties_for_class,
            discover_entity_properties,
            profile_property,
            check_shared_context
        ],
        output_key="ontology_insights"
    )
```

### 4.2 Progressive QueryBuilder
**File**: `adk_agents/agents/query_builder.py`
```python
def create_query_builder() -> LlmAgent:
    """Create QueryBuilder with progressive query construction"""
    
    instruction = """
    You build SPARQL queries progressively, starting simple and adding complexity.
    
    Query Building Process:
    1. Start with basic pattern matching
    2. Test the query with execute_test_query (limit 5)
    3. If results found, progressively add:
       - Filters
       - Aggregations
       - Grouping
       - Ordering
    4. Use cached query patterns from shared context
    
    CRITICAL Rules:
    - Always use prefix: mes_ontology_populated:
    - Timestamps are LITERALS, not IRIs - never use FILTER(ISIRI(?timestamp))
    - Add DISTINCT to prevent duplicates unless aggregating
    - Test each progression before adding more complexity
    
    Available query patterns:
    {query_patterns}
    """
    
    return LlmAgent(
        name="QueryBuilder",
        model="gemini-2.0-flash", 
        instruction=dynamic_instruction,
        tools=[
            build_query_progressively,
            execute_test_query,
            analyze_query_failure,
            get_query_patterns
        ],
        output_key="query_result"
    )
```

## Phase 5: Add Performance Monitoring (Week 5)

### 5.1 Create Performance Monitor
**File**: `adk_agents/monitoring/performance_monitor.py`
```python
from dataclasses import dataclass
from typing import Dict, List
import time

@dataclass
class PerformanceMetrics:
    agent_name: str
    operation: str
    start_time: float
    end_time: float
    tokens_used: int
    query_count: int
    cache_hits: int
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    @property
    def efficiency_score(self) -> float:
        # Higher cache hits and lower tokens = better
        if self.tokens_used == 0:
            return 0.0
        cache_ratio = self.cache_hits / max(1, self.query_count)
        return (cache_ratio * 1000) / self.tokens_used

class PerformanceMonitor:
    """Monitor agent performance and suggest optimizations"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.token_budget = 10000
        self.tokens_used = 0
        
    def start_operation(self, agent_name: str, operation: str) -> str:
        """Start tracking an operation"""
        op_id = f"{agent_name}_{operation}_{time.time()}"
        return op_id
        
    def end_operation(self, op_id: str, tokens: int, 
                     queries: int, cache_hits: int):
        """End tracking and analyze performance"""
        parts = op_id.split("_")
        agent_name = parts[0]
        operation = parts[1]
        start_time = float(parts[2])
        
        metric = PerformanceMetrics(
            agent_name=agent_name,
            operation=operation,
            start_time=start_time,
            end_time=time.time(),
            tokens_used=tokens,
            query_count=queries,
            cache_hits=cache_hits
        )
        
        self.metrics.append(metric)
        self.tokens_used += tokens
        
        # Check if optimization needed
        if self.tokens_used > self.token_budget * 0.8:
            return self.suggest_optimizations()
        
        return None
    
    def suggest_optimizations(self) -> Dict[str, Any]:
        """Analyze metrics and suggest optimizations"""
        
        # Find inefficient operations
        inefficient = [m for m in self.metrics if m.efficiency_score < 0.1]
        
        suggestions = []
        if inefficient:
            worst = min(inefficient, key=lambda m: m.efficiency_score)
            suggestions.append(
                f"Agent {worst.agent_name} is inefficient. "
                f"Used {worst.tokens_used} tokens with only "
                f"{worst.cache_hits}/{worst.query_count} cache hits"
            )
        
        # Check for repeated operations
        op_counts = {}
        for m in self.metrics:
            key = f"{m.agent_name}:{m.operation}"
            op_counts[key] = op_counts.get(key, 0) + 1
        
        repeated = {k: v for k, v in op_counts.items() if v > 3}
        if repeated:
            suggestions.append(
                f"Repeated operations detected: {repeated}. "
                "Consider caching or combining operations"
            )
        
        return {
            "token_usage": f"{self.tokens_used}/{self.token_budget}",
            "suggestions": suggestions,
            "should_summarize": self.tokens_used > self.token_budget * 0.9
        }
```

### 5.2 Integration with Callbacks
**File**: `adk_agents/agents/monitored_orchestrator.py`
```python
def create_monitored_orchestrator() -> LlmAgent:
    """Orchestrator with performance monitoring"""
    
    monitor = PerformanceMonitor()
    
    def on_before_model(callback_context: CallbackContext, 
                       request: LlmRequest) -> Optional[Content]:
        """Track model calls"""
        op_id = monitor.start_operation(
            callback_context.agent_name,
            "model_call"
        )
        callback_context.state["_current_op_id"] = op_id
        return None
    
    def on_after_model(callback_context: CallbackContext,
                      request: LlmRequest,
                      response: LlmResponse) -> None:
        """Analyze model performance"""
        op_id = callback_context.state.get("_current_op_id")
        if op_id and response.usage_metadata:
            tokens = response.usage_metadata.total_token_count
            
            # Count queries and cache hits from state
            queries = callback_context.state.get("_query_count", 0)
            cache_hits = callback_context.state.get("_cache_hits", 0)
            
            optimization = monitor.end_operation(
                op_id, tokens, queries, cache_hits
            )
            
            if optimization and optimization["should_summarize"]:
                # Switch to summary mode
                callback_context.state["_summary_mode"] = True
                callback_context.actions.skip_summarization = False
    
    return LlmAgent(
        name="MonitoredOrchestrator",
        model="gemini-2.0-flash",
        instruction=get_monitored_instruction,
        callbacks={
            "on_before_model": on_before_model,
            "on_after_model": on_after_model
        },
        tools=[transfer_to_agent_with_context, get_performance_summary]
    )
```

## Implementation Timeline

### Week 1: SPARQL Query Fixes
- Implement SPARQLQueryBuilder with correct prefixes
- Update query tools to handle timestamps as literals
- Add query validation and optimization
- Test with existing queries from trace.json

### Week 2: Context Sharing
- Implement SharedAgentContext
- Update all agents to use shared context
- Add context serialization to state
- Test context persistence across agent transfers

### Week 3: Query Intelligence  
- Add data profiling tools
- Implement progressive query building
- Create query pattern library
- Test with complex analytical queries

### Week 4: Agent Enhancement
- Rewrite agent instructions with context awareness
- Implement proper handoff mechanisms
- Add fallback strategies for common failures
- Integration testing of full agent pipeline

### Week 5: Performance & Polish
- Add performance monitoring
- Implement token budget management
- Create optimization suggestions
- Final testing and documentation

## Success Metrics

1. **Query Success Rate**: >95% of SPARQL queries return results
2. **Token Efficiency**: 50% reduction in tokens per analysis
3. **Cache Hit Rate**: >40% for repeated explorations
4. **Analysis Speed**: 3x faster for common patterns
5. **Error Recovery**: Automatic handling of 90% of known issues

## Testing Strategy

### Unit Tests
- Test each query builder method with known data
- Validate context serialization/deserialization
- Test performance metric calculations

### Integration Tests
- Full agent conversation flows
- Context sharing between agents
- Query optimization pipeline
- Performance monitoring accuracy

### End-to-End Tests
- Complete analysis scenarios from trace.json
- Multi-agent collaboration patterns
- Error recovery workflows
- Performance under token constraints

## Deployment Considerations

1. **Backward Compatibility**
   - Ensure existing queries still work
   - Migrate state format gradually
   - Provide fallback for missing context

2. **Configuration**
   - Make namespace configurable
   - Allow performance thresholds adjustment
   - Enable/disable caching per deployment

3. **Monitoring**
   - Log all query patterns for analysis
   - Track cache hit rates
   - Monitor token usage trends
   - Alert on repeated failures

## Conclusion

This implementation plan addresses all major issues identified in the trace analysis:
- SPARQL queries will properly handle timestamps and aggregation
- Agents will share context to avoid redundant work
- Performance monitoring will prevent token waste
- Progressive query building will improve success rates

The phased approach ensures we can validate improvements incrementally while maintaining system stability.