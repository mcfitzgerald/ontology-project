# ADK Agents System Improvements

## Executive Summary

Analysis of the ADK agents system revealed fundamental architectural issues causing excessive API calls, rate limit errors, and poor query performance. The system made 17+ SPARQL queries to answer a simple question about available data, ultimately hitting Vertex AI rate limits. The root cause is inefficient context usage and poor separation of concerns between agents.

## Current Issues

### 1. Excessive Query Volume
- **Problem**: 17+ queries executed for a simple "what data is available?" question
- **Impact**: Hit Vertex AI rate limit (429 error) after 25 requests in 2.6 minutes
- **Root Cause**: Agent discovering ontology structure through trial-and-error queries instead of using pre-loaded context

### 2. Poor Query Success Rate
- **Problem**: Only 23.5% of SPARQL queries succeed
- **Impact**: Wasted API calls and increased latency
- **Root Cause**: 
  - Incorrect query patterns for Owlready2
  - Discovering schema through queries that return 0 results
  - Not leveraging known working patterns

### 3. Context Management Issues
- **Problem**: Large context loaded but not effectively used
- **Impact**: High token usage without benefit
- **Root Cause**: Agents have context in prompts but still perform discovery queries

### 4. Architectural Flaws
- **Problem**: Poor separation of concerns between agents
- **Impact**: SPARQLExecutor doing schema discovery instead of query execution
- **Root Cause**: Responsibilities not clearly defined

## Recommended Fixes

### 1. Fix Context Loading and Usage

**Current State**: Context is loaded into prompts but agents don't use it effectively

**Proposed Solution**:
```python
# In app.py or context_loader.py
class OntologyKnowledge:
    def __init__(self):
        self.classes = self._parse_ttl_classes()
        self.properties = self._parse_ttl_properties()
        self.relationships = self._parse_ttl_relationships()
        self.working_patterns = self._load_query_patterns()
    
    def get_available_data_summary(self):
        """Return pre-computed summary of available data"""
        return {
            "equipment_types": ["Filler", "Packer", "Palletizer"],
            "metrics": ["OEE", "Availability", "Performance", "Quality"],
            "products": self.get_product_list(),
            "time_range": self.get_data_timerange()
        }
```

**Benefits**:
- Eliminate discovery queries
- Instant responses for schema questions
- Reduce API calls by 80%+

### 2. Redesign Agent Responsibilities

**Current State**: Unclear boundaries, SPARQLExecutor discovers schema

**Proposed Solution**:

#### ConversationOrchestrator Responsibilities:
- Answer all schema/structure questions directly from context
- Plan query strategy based on user intent
- Only delegate when actual data retrieval needed
- Provide summaries without querying when possible

#### SPARQLExecutor Responsibilities:
- Execute only well-formed, validated queries
- No schema discovery (already known)
- Focus on query optimization and error recovery
- Maintain query result cache

**Implementation**:
```python
# In conversation_orchestrator.py
def can_answer_without_query(self, user_question):
    """Determine if question can be answered from context"""
    if any(term in user_question.lower() for term in 
           ['what data', 'available', 'structure', 'schema']):
        return True, self.ontology_knowledge.get_available_data_summary()
    return False, None
```

### 3. Implement Query Planning

**Current State**: Reactive querying with no planning

**Proposed Solution**:
```python
class QueryPlanner:
    def __init__(self, ontology_knowledge):
        self.ontology = ontology_knowledge
        self.templates = self._load_query_templates()
    
    def plan_queries_for_intent(self, user_intent):
        """Generate optimal query plan based on intent"""
        if intent_type == "explore_oee":
            return [
                self.templates.get_equipment_oee_summary(),
                self.templates.get_oee_time_series()
            ]
        # Don't discover - we know what's available
```

**Benefits**:
- Reduce queries by 70%+
- Higher success rate (using proven patterns)
- Batch related queries

### 4. Add Comprehensive Caching

**Current State**: Limited caching, rediscovering same information

**Proposed Solution**:
```python
class MultiLevelCache:
    def __init__(self):
        self.static_cache = {}  # Ontology structure, never changes
        self.dynamic_cache = TTLCache(maxsize=1000, ttl=300)  # Query results
        self.pattern_cache = {}  # Successful query patterns
    
    def get_or_compute(self, key, compute_fn, cache_type='dynamic'):
        """Get from cache or compute and store"""
        if cache_type == 'static' and key in self.static_cache:
            return self.static_cache[key]
        # ... implementation
```

**Cache Layers**:
1. **Static Cache**: Ontology structure, equipment list, product info
2. **Dynamic Cache**: Query results with 5-minute TTL
3. **Pattern Cache**: Successful query templates

### 5. Implement Proper Rate Limiting

**Current State**: Rate limiter exists but not preventing 429 errors

**Proposed Solution**:
```python
# In sparql_tool.py
class EnhancedRateLimiter:
    def __init__(self, rpm=48, burst_size=5):
        self.semaphore = asyncio.Semaphore(burst_size)
        self.min_interval = 60.0 / rpm
        self.last_request = 0
    
    async def acquire(self):
        async with self.semaphore:
            # Enforce minimum interval
            now = time.time()
            wait_time = self.last_request + self.min_interval - now
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self.last_request = time.time()
```

**Configuration** (add to .env):
```bash
# Rate Limiting Configuration
RATE_LIMIT_ENABLED=TRUE
RATE_LIMIT_RPM=48  # 80% of Vertex AI's 60 RPM limit
RATE_LIMIT_THROTTLE_MS=1250
RATE_LIMIT_BURST_SIZE=5
```

### 6. Optimize Token Usage

**Current State**: Full conversation history included, increasing tokens

**Proposed Solution**:
1. **Conversation Summarization**: Replace old turns with summaries
2. **Context Compression**: Only include relevant ontology sections
3. **Result Truncation**: Limit large result sets in context
4. **Selective History**: Only include successful queries in history

### 7. Pre-compute Common Analyses

**Current State**: Every question triggers new queries

**Proposed Solution**:
```python
# Run on startup or schedule
class PreComputedInsights:
    def __init__(self):
        self.equipment_summary = self._compute_equipment_summary()
        self.product_margins = self._compute_product_margins()
        self.common_patterns = self._identify_common_patterns()
    
    def refresh(self):
        """Refresh pre-computed data every hour"""
        # ... implementation
```

## Implementation Priority

1. **Critical (Week 1)**:
   - Fix rate limiting implementation
   - Add RATE_LIMIT configuration to .env
   - Implement static context caching

2. **High (Week 2)**:
   - Redesign agent responsibilities
   - Implement query planning
   - Add conversation summarization

3. **Medium (Week 3)**:
   - Pre-compute common analyses
   - Enhance caching layers
   - Optimize token usage

4. **Low (Week 4)**:
   - Add monitoring/metrics
   - Performance optimization
   - Advanced query patterns

## Expected Outcomes

After implementing these improvements:
- **Query Reduction**: From 17+ to 2-3 queries per question
- **Success Rate**: From 23.5% to 90%+ 
- **Response Time**: 5x faster for common questions
- **Rate Limits**: No more 429 errors
- **Token Usage**: 50% reduction
- **User Experience**: Instant answers for structure questions

## Monitoring and Metrics

Track these KPIs to measure improvement:
- Queries per conversation turn
- Query success rate
- Cache hit rate
- Average response time
- Rate limit violations
- Token usage per turn

## Testing Plan

1. **Unit Tests**: Cache behavior, query planning logic
2. **Integration Tests**: Agent communication, rate limiting
3. **Load Tests**: Verify rate limit compliance
4. **User Tests**: Common question scenarios

## Migration Strategy

1. Implement fixes in parallel branch
2. Test with common scenarios
3. A/B test with subset of users
4. Monitor metrics closely
5. Full rollout after validation