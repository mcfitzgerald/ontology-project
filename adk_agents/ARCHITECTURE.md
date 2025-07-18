# ADK Agents Architecture Reference

## Overview

The ADK (Agent Development Kit) agents system is a conversational manufacturing analytics platform built on Google's Agent Development Kit framework. It discovers multi-million dollar opportunities in manufacturing data through exploratory analysis of an OWL ontology populated with MES (Manufacturing Execution System) data.

## System Architecture

### Core Design Principles

1. **Simplified Two-Agent System**: Streamlined from complex multi-agent architectures to just two specialized agents
2. **Conversational Partnership**: Agents partner with users through exploratory analysis rather than rigid query-response
3. **Financial-First**: Every operational metric connects to business impact and ROI
4. **Progressive Discovery**: Build understanding through exploration, not assumptions
5. **Rate-Limited & Resilient**: Built-in protection against API limits with automatic throttling
6. **Observable**: Comprehensive logging with analysis tools for diagnostics

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     User Interface                       │
│                  (ADK Web/Terminal)                      │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   app.py (Entry Point)                   │
│  - Initializes agents with tools                         │
│  - Creates shared components                             │
│  - Exports root_agent for ADK discovery                  │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
┌─────────────────────┐       ┌─────────────────────┐
│ Conversation        │       │ SPARQL Executor     │
│ Orchestrator        │◄──────┤ (Specialized Agent) │
│ (Main Agent)        │       │                     │
├─────────────────────┤       ├─────────────────────┤
│ - Discovery phase   │       │ - Query execution   │
│ - Pattern finding   │       │ - Error recovery    │
│ - Quantification    │       │ - Pattern learning  │
│ - Recommendations  │       │ - Query optimization│
└──────┬──────────────┘       └──────┬──────────────┘
       │                             │
       ▼                             ▼
┌─────────────────────┐       ┌─────────────────────┐
│ Python Analysis     │       │ SPARQL Tool         │
│ Tool                │       │                     │
├─────────────────────┤       ├─────────────────────┤
│ - Statistical calc  │       │ - Async execution   │
│ - Visualizations    │       │ - Owlready2 adapter │
│ - Financial models  │       │ - Query caching     │
└─────────────────────┘       └──────┬──────────────┘
                                     │
                              ┌──────▼──────────────┐
                              │ SPARQL Endpoint     │
                              │ (FastAPI Server)    │
                              └──────┬──────────────┘
                                     │
                              ┌──────▼──────────────┐
                              │ OWL Ontology        │
                              │ (Owlready2)         │
                              └─────────────────────┘
```

## Component Details

### 1. Entry Point (`app.py`)

```python
# Key responsibilities:
- Initialize Vertex AI or API key authentication
- Create shared infrastructure (context loader, query cache)
- Wire up agents with their specific tools
- Export root_agent for ADK framework discovery
```

### 2. Conversation Orchestrator (`agents/conversation_orchestrator.py`)

**Purpose**: Main agent that partners with users through the analysis journey

**Key Features**:
- Manages 4-phase analysis workflow
- Delegates SPARQL queries to specialized executor
- Direct access to Python analysis tools
- Maintains conversational state

**Analysis Phases**:
1. **Discovery**: Explore available data, understand structure
2. **Pattern Recognition**: Find anomalies, correlations, trends
3. **Quantification**: Calculate business impact in dollars
4. **Recommendations**: Prioritize by ROI, suggest improvements

**Communication Style**:
- Conversational and exploratory
- Thinks out loud about discoveries
- Celebrates findings with users
- Always connects to business value

### 3. SPARQL Executor (`agents/sparql_executor.py`)

**Purpose**: Specialized agent for SPARQL query execution with Owlready2 compatibility

**Key Features**:
- Strict adherence to Owlready2 SPARQL rules
- Query pattern learning and caching
- Automatic error recovery
- Common fix implementations

**Owlready2 Adaptations**:
- No angle brackets in URIs
- Full namespace prefix required: `mes_ontology_populated:`
- No PREFIX declarations
- FILTER(ISIRI()) for entity variables

### 4. Configuration System

#### Settings (`config/settings.py`)
```python
# Environment-based configuration
GOOGLE_GENAI_USE_VERTEXAI=TRUE  # or FALSE for API key
GOOGLE_CLOUD_PROJECT=your-project
GOOGLE_CLOUD_LOCATION=us-east1
SPARQL_ENDPOINT=http://localhost:8000/sparql/query

# Model configuration
MODEL_NAME = "gemini-2.0-flash-exp"
```

#### System Prompts (`config/prompts/system_prompts.py`)
- Specialized prompts for each agent role
- Owlready2-specific SPARQL rules
- Business value focus
- Analysis patterns from proven discoveries

### 5. Context Management

#### Context Loader (`utils/context_loader.py`)
**Loads and manages**:
- TTL mindmap of ontology structure
- SPARQL reference documentation
- Learned query patterns
- Data catalogue summaries
- Business context annotations

#### Shared Context (`context/shared_context.py`)
**Maintains**:
- Query success/failure history
- Discovered properties cache
- Known data patterns
- Session state

### 6. Tools

#### SPARQL Tool (`tools/sparql_tool.py`)
```python
# Features:
- Async execution against SPARQL endpoint
- Automatic Owlready2 adaptation
- Built-in retry logic
- Query result caching
- Pre-built helper functions
```

#### Python Analysis Tool (`tools/python_analysis.py`)
```python
# Capabilities:
- Statistical analysis with pandas, numpy
- Visualization with matplotlib, seaborn
- Financial calculations
- Base64-encoded plot output
```

#### SPARQL Builder (`tools/sparql_builder.py`)
```python
# Pre-built templates for:
- Pareto analysis (80/20 rule)
- Time series analysis
- OEE performance tracking
- Defect pattern analysis
- Equipment correlation
```

#### Analysis Tools (`tools/analysis_tools.py`)
```python
# Advanced analysis functions:
- Temporal pattern analysis
- Financial impact calculation
- Anomaly detection
- ROI scenario modeling
```

### 7. Utilities

#### Financial Calculator (`utils/financial_calc.py`)
**Calculations**:
- OEE impact → production volume → revenue
- Downtime cost modeling
- Quality defect financial impact
- ROI scenarios with payback periods

#### Owlready2 Adapter (`utils/owlready2_adapter.py`)
**Critical adaptations**:
```sparql
# Before adaptation:
PREFIX mes: <http://example.org/mes#>
SELECT ?equipment WHERE {
  ?equipment a mes:Equipment .
}

# After adaptation:
SELECT ?equipment WHERE {
  ?equipment a mes_ontology_populated:Equipment .
  FILTER(ISIRI(?equipment))
}
```

#### Query Cache (`utils/query_cache.py`)
**Learning mechanism**:
- Stores successful queries with purpose
- Tracks query failures and fixes
- Enables pattern reuse
- Improves over time

#### Log Parser (`utils/log_parser.py`)
**Smart log processing**:
- Extracts meaningful information from ADK logs
- Truncates large SPARQL results (max 10 rows)
- Groups conversations and tool calls
- Identifies LLM requests and responses
- Generates session summaries with key metrics

#### Log Analyzer (`utils/log_analyzer.py`)
**Pattern detection and diagnostics**:
- Analyzes parsed logs for issues
- Detects rate limit violations
- Calculates optimal throttling settings
- Identifies query failure patterns
- Generates actionable recommendations

#### Rate Limiter (`utils/rate_limiter.py`)
**Token bucket algorithm**:
- Prevents API rate limit errors
- Default: 48 RPM (80% of Vertex AI limit)
- Configurable burst capacity
- Integrated into SPARQL tool
- Real-time statistics tracking

## Data Flow

### 1. User Query Processing
```
User Question 
→ Conversation Orchestrator (analyzes intent)
→ Determines if SPARQL needed
→ Delegates to SPARQL Executor OR uses Python tool
```

### 2. SPARQL Query Flow
```
SPARQL Executor receives request
→ Checks query cache for similar patterns
→ Builds/adapts query with Owlready2 rules
→ Executes against endpoint
→ Handles errors with common fixes
→ Caches successful patterns
→ Returns results to Orchestrator
```

### 3. Analysis Flow
```
Orchestrator receives data
→ Python Analysis Tool processes
→ Financial calculations applied
→ Visualizations generated
→ Insights presented conversationally
```

## Key Design Patterns

### 1. Progressive Complexity
- Start with simple queries
- Build understanding incrementally
- Add complexity based on findings

### 2. Financial-First Analysis
- Every metric ties to dollars
- ROI drives prioritization
- Quantify improvement opportunities

### 3. Pattern Recognition Focus
- Temporal patterns (hourly, shift-based)
- Quality correlations
- Equipment cascade effects
- Micro-stop aggregation

### 4. Conversational UX
- Think out loud about discoveries
- Celebrate findings with users
- Explain reasoning
- Build partnership

## Configuration Files

### Required Environment Variables (`.env`)
```bash
# Vertex AI Configuration (Recommended)
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-east1

# OR API Key Configuration
GOOGLE_API_KEY=your-api-key
GOOGLE_GENAI_USE_VERTEXAI=FALSE

# SPARQL Configuration
SPARQL_ENDPOINT=http://localhost:8000/sparql/query
SPARQL_TIMEOUT=30

# Rate Limiting (NEW)
RATE_LIMIT_ENABLED=TRUE
RATE_LIMIT_RPM=48  # 80% of Vertex AI's 60 RPM limit
RATE_LIMIT_THROTTLE_MS=1250
RATE_LIMIT_BURST_SIZE=5
```

### Context Files
- `/Context/ttl_mindmap.ttl` - Ontology structure
- `/Context/owlready2_sparql_master_reference.md` - SPARQL patterns
- `/Context/data_catalogue_summary.md` - Data overview
- `learned_patterns.json` - Cached successful queries

## Common SPARQL Patterns

### Basic Entity Query
```sparql
SELECT ?equipment ?oee WHERE {
  ?equipment a mes_ontology_populated:Equipment .
  ?equipment mes_ontology_populated:hasOEEScore ?oee .
  FILTER(ISIRI(?equipment))
  FILTER(?oee < 0.85)
}
```

### Time Series Analysis
```sparql
SELECT ?hour (AVG(?oee) as ?avg_oee) WHERE {
  ?event a mes_ontology_populated:ProductionEvent .
  ?event mes_ontology_populated:hasTimestamp ?timestamp .
  ?event mes_ontology_populated:hasOEEScore ?oee .
  BIND(HOURS(?timestamp) as ?hour)
}
GROUP BY ?hour
ORDER BY ?hour
```

### Financial Impact Query
```sparql
SELECT ?equipment ?product 
       (SUM(?volume * ?margin) as ?lost_revenue) WHERE {
  ?equipment mes_ontology_populated:produces ?product .
  ?product mes_ontology_populated:hasUnitMargin ?margin .
  ?event mes_ontology_populated:hasEquipment ?equipment .
  ?event mes_ontology_populated:hasDowntimeMinutes ?downtime .
  ?event mes_ontology_populated:hasProductionVolume ?volume .
  FILTER(?downtime > 0)
}
GROUP BY ?equipment ?product
ORDER BY DESC(?lost_revenue)
```

## Proven Analysis Patterns

### 1. Capacity Optimization Pattern
- Find equipment below 85% OEE benchmark
- Calculate production gap
- Quantify revenue opportunity
- Prioritize by financial impact

### 2. Temporal Clustering Pattern
- Identify issues within 15-minute windows
- Find shift-based patterns
- Correlate with external factors
- Target root causes

### 3. Quality-Cost Tradeoff Pattern
- Focus on high-margin products
- Analyze defect rates by value
- Calculate scrap cost impact
- Optimize quality controls

### 4. Equipment Cascade Pattern
- Trace upstream/downstream impacts
- Identify bottleneck propagation
- Quantify system-wide losses
- Target critical path equipment

### 5. Micro-Stop Aggregation Pattern
- Aggregate 1-5 minute stops
- Calculate cumulative impact
- Often reveals hidden losses
- Low-cost improvement targets

## Extension Points

### Adding New Tools
1. Create tool in `tools/` directory
2. Use `FunctionTool` from Google ADK
3. Attach to appropriate agent in `app.py`
4. Update agent prompts if needed

### Adding New Agents
1. Create agent in `agents/` directory
2. Define specialized prompt
3. Attach relevant tools
4. Wire up in `app.py`

### Adding Analysis Patterns
1. Document pattern in `config/prompts/analysis_patterns.py`
2. Add SPARQL templates to `sparql_builder.py`
3. Implement calculations in `financial_calc.py`
4. Update context documentation

## Best Practices

### 1. Query Development
- Always test in SPARQL endpoint first
- Use full namespace prefix
- Include FILTER(ISIRI()) for entities
- Start simple, add complexity

### 2. Financial Modeling
- Use conservative estimates
- Document assumptions
- Provide ranges, not just point estimates
- Include implementation costs

### 3. Agent Communication
- Keep responses conversational
- Explain reasoning
- Celebrate discoveries
- Always connect to business value

### 4. Error Handling
- Graceful degradation
- Helpful error messages
- Automatic recovery attempts
- Learn from failures

## Troubleshooting

See the comprehensive [Troubleshooting Guide](TROUBLESHOOTING.md) for detailed diagnostics and solutions.

### Quick Reference

1. **Rate Limit Errors (429)**
   ```bash
   # Analyze session for rate issues
   python adk_agents/utils/log_analyzer.py adk_web.log
   ```

2. **SPARQL Query Failures**
   - Use full prefix: `mes_ontology_populated:`
   - No angle brackets in URIs
   - Include `FILTER(ISIRI(?var))` for entities

3. **High Token Usage**
   ```bash
   # View truncated logs
   python adk_agents/utils/log_parser.py adk_web.log
   ```

4. **System Health Check**
   ```bash
   curl http://localhost:8000/health
   ```

## Performance Optimization

### 1. Query Optimization
- Use query cache effectively
- Limit result sets with LIMIT
- Add selective filters early
- Use aggregations server-side

### 2. Context Management
- Load context once at startup
- Cache parsed structures
- Minimize context in prompts
- Use dynamic context building

### 3. Parallel Processing
- Batch independent queries
- Use async execution
- Process results concurrently
- Cache computed results

## References

- [Google Agent Development Kit (ADK)](https://github.com/googleapis/agent-dev-kit)
- [Owlready2 Documentation](https://owlready2.readthedocs.io/)
- [SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/)
- [Manufacturing KPIs and OEE](https://www.oee.com/)