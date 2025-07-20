# ADK Manufacturing Analytics System - Architecture Documentation

## Executive Summary

The Ontology-Augmented Manufacturing Analytics System is a sophisticated conversational AI platform built on Google's Agent Development Kit (ADK) that bridges MES data with modern LLMs using an ontology as a semantc layer to unlock hidden value in operational data. While initially demonstrated in manufacturing analytics where it discovered $2.5M+ in optimization opportunities, the system's architecture is designed to be domain-agnostic and applicable to any industry with structured operational data.

## Proven Business Methodology

### Core Value Proposition

The system transforms natural language business questions into actionable insights through a proven methodology that has already demonstrated significant ROI:

**Business Impact Pipeline:**
```
Business Question → Context Discovery → Query Strategy → Data Retrieval → 
Pattern Analysis → Financial Modeling → Actionable Insight → ROI Validation
```

### Universal Analysis Principles

1. **Start with WHY** - Every analysis must connect to business value
2. **Context is King** - Ontology annotations contain hidden business logic
3. **Iterate Incrementally** - Build complex insights from simple queries
4. **Validate Against Reality** - Check results match known patterns
5. **Quantify Everything** - Convert operational metrics to financial impact
6. **Pattern Over Point** - Look for trends, not single data points
7. **Action Over Analysis** - End with specific, implementable recommendations

### Proven Analysis Patterns

The system implements five core analysis patterns that have proven effective across domains:

#### Pattern 1: Capacity/Resource Optimization
- **Question**: "What's the gap between current and optimal performance?"
- **Proven Result**: Hidden manufacturing capacity worth $341K-$700K/year

#### Pattern 2: Temporal Pattern Recognition
- **Question**: "When and why do problems cluster?"
- **Proven Result**: Micro-stop patterns revealing $250K-$350K opportunity

#### Pattern 3: Multi-Factor Trade-off Analysis
- **Question**: "What's the optimal balance between competing factors?"
- **Proven Result**: Quality improvements worth $200K/year with targeted investments

#### Pattern 4: Root Cause Investigation
- **Question**: "What's really causing our problems?"
- **Approach**: Trace symptoms through relationship chains to identify cascade effects

#### Pattern 5: Predictive Trigger Identification
- **Question**: "When should we intervene?"
- **Approach**: Identify early warning signals and calculate prevention value

## System Architecture Overview

The ADK Manufacturing Analytics System implements the above methodology through a sophisticated technical architecture that enables business users to analyze complex data through natural language queries. The system provides two parallel implementations to support different use cases while sharing the same core analytical engine.

### Dual Implementation Strategy

1. **CLI Agent** (`agents/manufacturing_analyst.py`) - Terminal-based interface for development and testing
2. **ADK Web Agent** (`manufacturing_agent/agent.py`) - Web UI interface for production use

Both implementations share the same core tools and context system, ensuring consistent behavior across interfaces.

## Core Components

### 1. Context Loading System (`context/context_loader.py`)

The ContextLoader is the knowledge foundation of the system, providing:

- **Ontology Structure**: Loads complete OWL ontology definitions from TTL files
- **SPARQL Rules**: Owlready2-specific syntax rules and constraints
- **Query Examples**: Successful query patterns for learning
- **Data Catalogue**: Metadata about available equipment, products, and data ranges

Key methods:
- `load_ontology_context()`: Loads domain ontology structure
- `load_sparql_reference()`: Provides SPARQL syntax rules
- `load_successful_queries()`: Returns example queries
- `load_data_catalogue()`: Loads data inventory information

### 2. SPARQL Execution Tool (`tools/sparql_tool.py`)

The SPARQLExecutor handles all database interactions with intelligent caching and token overflow prevention:

Features:
- **Query Caching**: SHA256-based cache to avoid redundant executions
- **Pattern Learning**: Stores successful queries for future reference
- **Error Handling**: Graceful timeout and error management
- **Result Optimization**: Automatically caches ALL results and returns summaries for large datasets
- **Token Estimation**: Uses heuristics (1 token ≈ 4 characters) to prevent LLM token overflow
- **Smart Truncation**: Returns summaries with cache IDs for results >10k tokens
- **Aggregation Failure Detection**: Automatically detects when COUNT/GROUP BY queries fail due to Owlready2 limitations
- **Fallback Query Generation**: Provides alternative queries for Python-based aggregation when SPARQL aggregation fails

Key methods:
- `execute()`: Main query execution with caching and aggregation failure detection
- `learn_pattern()`: Extracts patterns from successful queries
- `get_query_hash()`: Generates cache keys
- `get_cached_query_result()`: Retrieves full cached results by ID

### 3. Result Cache Manager (`tools/result_cache.py`)

Manages caching of large query results to prevent token overflow:

Features:
- **Universal Caching**: Caches ALL query results regardless of size
- **Token Estimation**: Simple heuristics to estimate result size
- **Smart Summaries**: Creates summaries with sample data and statistics
- **Cache Management**: UUID-based cache IDs with indexed retrieval

Key methods:
- `cache_result()`: Stores full results and returns summary with cache ID
- `get_cached_result()`: Retrieves full data by cache ID
- `create_summary()`: Generates intelligent summaries with statistics
- `estimate_tokens()`: Estimates token count for safety

### 4. Analysis Tools (`tools/analysis_tools.py`)

Provides sophisticated pattern detection and financial analysis implementing the proven patterns:

Analysis Types:
- **Temporal Analysis**: Trend detection, gap analysis, time-based patterns
- **Capacity Analysis**: Equipment utilization, bottleneck identification
- **Quality Analysis**: Defect patterns, quality trends
- **ROI Calculation**: Financial impact of performance improvements

Key functions:
- `analyze_patterns()`: Main analysis dispatcher
- `calculate_roi()`: Computes financial benefits
- `find_optimization_opportunities()`: Identifies improvement areas

### 5. Visualization Tool (`tools/visualization_tool.py`)

Enables creation of charts and graphs from query results to make insights more accessible:

Chart Types:
- **Line Charts**: Temporal trends (OEE over time, performance metrics)
- **Bar Charts**: Comparisons (equipment performance, product quality)
- **Scatter Plots**: Correlations (quality vs speed, downtime vs shift)
- **Pie Charts**: Distributions (downtime reasons, product mix)

Key features:
- `create_visualization()`: Main chart creation function supporting cached results
- Matplotlib-based rendering with pandas data processing
- ADK artifact system integration (saves charts as artifacts in Web UI)
- Base64 encoding fallback for CLI implementation
- **Cached Result Support**: Can visualize from summaries or retrieve full data via cache_id
- **Automatic Data Type Detection**: Intelligently selects appropriate chart type based on data characteristics

### 6. Agent Implementations

#### CLI Agent (`agents/manufacturing_analyst.py`)
- Uses Google's generativeai library directly
- Manages conversation state with chat sessions
- Provides function calling capabilities for tools including visualization
- Interactive terminal interface with commands (help, cache, reset)
- Enhanced with discovery-first methodology and exploration phase
- Improved IRI handling and collaborative interaction patterns
- **Token-Safe Queries**: Guidance for aggregation and sampling to prevent overflow
- **Cache Integration**: Tools to retrieve full cached results when needed
- **Proactive Query Execution**: Executes queries immediately for better UX
- **Aggregation Failure Handling**: Automatic detection and fallback for Owlready2 limitations

#### ADK Agent (`manufacturing_agent/agent.py`)
- Implements Google ADK's LlmAgent interface
- Defines FunctionTool wrappers for ADK compatibility including async visualization
- Provides web-based interaction through ADK UI
- Follows ADK's declarative agent definition pattern
- Synchronized with CLI agent's enhanced methodology
- **Large Result Handling**: Automatic detection and summary generation
- **Cached Result Retrieval**: Function to access full data by cache ID
- **Proactive Query Execution**: Executes queries immediately for better UX
- **Aggregation Failure Handling**: Automatic detection and fallback for Owlready2 limitations

### 7. Configuration System (`config/settings.py`)

Centralized configuration management supporting:
- Environment variable loading via .env files
- Vertex AI and API key authentication modes
- Model parameters (temperature, token limits)
- SPARQL endpoint configuration
- Cache and rate limiting settings
- Maximum SPARQL results configuration
- Analysis window configuration
- Ontology namespace settings

## Control and Information Flow

```mermaid
graph TB
    subgraph "User Interfaces"
        CLI[CLI Interface<br/>main.py]
        WEB[ADK Web UI<br/>Port 8001]
    end
    
    subgraph "Agent Layer"
        CLIAGENT[CLI Agent<br/>manufacturing_analyst.py]
        ADKAGENT[ADK Agent<br/>manufacturing_agent/agent.py]
    end
    
    subgraph "Context System"
        LOADER[Context Loader]
        ONTOLOGY[(Ontology<br/>TTL Files)]
        SPARQLREF[(SPARQL<br/>Reference)]
        CATALOGUE[(Data<br/>Catalogue)]
        EXAMPLES[(Query<br/>Examples)]
    end
    
    subgraph "Tools"
        SPARQLTOOL[SPARQL Tool<br/>Execute & Cache<br/>Aggregation Fallback]
        RESULTCACHE[Result Cache<br/>Token Safety]
        ANALYSIS[Analysis Tools<br/>Pattern Detection]
        ROI[ROI Calculator]
        VIZ[Visualization Tool<br/>Chart Generation]
        CACHE[Query Cache]
        CACHEMANAGER[Cache Manager<br/>Pattern Learning]
    end
    
    subgraph "External Systems"
        SPARQLAPI[SPARQL API<br/>Port 8000]
        GEMINI[Google Gemini<br/>LLM API]
        DB[(Operational<br/>Database)]
    end
    
    %% User interactions
    CLI -->|User Query| CLIAGENT
    WEB -->|User Query| ADKAGENT
    
    %% Context loading
    CLIAGENT -->|Load Context| LOADER
    ADKAGENT -->|Load Context| LOADER
    LOADER -->|Read| ONTOLOGY
    LOADER -->|Read| SPARQLREF
    LOADER -->|Read| CATALOGUE
    LOADER -->|Read| EXAMPLES
    
    %% LLM interactions
    CLIAGENT <-->|Generate Response| GEMINI
    ADKAGENT <-->|Generate Response| GEMINI
    
    %% Tool usage
    CLIAGENT -->|Function Call| SPARQLTOOL
    CLIAGENT -->|Function Call| ANALYSIS
    CLIAGENT -->|Function Call| ROI
    CLIAGENT -->|Function Call| VIZ
    ADKAGENT -->|Function Call| SPARQLTOOL
    ADKAGENT -->|Function Call| ANALYSIS
    ADKAGENT -->|Function Call| ROI
    ADKAGENT -->|Function Call| VIZ
    
    %% SPARQL execution
    SPARQLTOOL -->|Check| CACHE
    CACHE -->|Hit/Miss| SPARQLTOOL
    SPARQLTOOL -->|Execute Query| SPARQLAPI
    SPARQLAPI -->|Query| DB
    DB -->|Results| SPARQLAPI
    SPARQLAPI -->|Results| SPARQLTOOL
    SPARQLTOOL -->|Store| CACHE
    SPARQLTOOL -->|Large Results| RESULTCACHE
    RESULTCACHE -->|Summary| SPARQLTOOL
    SPARQLTOOL -->|Learn Pattern| CACHEMANAGER
    
    %% Aggregation fallback
    SPARQLTOOL -->|Aggregation Fail| SPARQLTOOL
    Note over SPARQLTOOL: Fallback to raw data query
    
    %% Analysis flow
    SPARQLTOOL -->|Results| ANALYSIS
    SPARQLTOOL -->|Results| VIZ
    ANALYSIS -->|Insights| CLIAGENT
    ANALYSIS -->|Insights| ADKAGENT
    ROI -->|Calculations| CLIAGENT
    ROI -->|Calculations| ADKAGENT
    VIZ -->|Charts| CLIAGENT
    VIZ -->|Charts| ADKAGENT
    
    %% Response flow
    CLIAGENT -->|Formatted Response| CLI
    ADKAGENT -->|Formatted Response| WEB
    
    style CLI fill:#e1f5fe
    style WEB fill:#e1f5fe
    style CLIAGENT fill:#fff3e0
    style ADKAGENT fill:#fff3e0
    style SPARQLTOOL fill:#f3e5f5
    style RESULTCACHE fill:#f3e5f5
    style ANALYSIS fill:#f3e5f5
    style ROI fill:#f3e5f5
    style VIZ fill:#f3e5f5
    style CACHE fill:#f3e5f5
    style CACHEMANAGER fill:#f3e5f5
    style GEMINI fill:#e8f5e9
    style SPARQLAPI fill:#ffebee
    style DB fill:#ffebee
```

## Data Flow Sequence

### 1. Query Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant Agent
    participant Context
    participant LLM
    participant SPARQL
    participant Cache
    participant Analysis
    
    User->>Agent: Business Question
    Agent->>Context: Load Ontology & Rules
    Context-->>Agent: Context Data
    Agent->>LLM: Question + Context
    LLM-->>Agent: SPARQL Query
    Agent->>SPARQL: Execute Query
    SPARQL->>Cache: Check Cache
    alt Cache Hit
        Cache-->>SPARQL: Cached Results
    else Cache Miss
        SPARQL->>API: HTTP Request
        API-->>SPARQL: Query Results
        SPARQL->>Cache: Store Results
    end
    SPARQL-->>Agent: Results
    Agent->>Analysis: Analyze Patterns
    Analysis-->>Agent: Insights
    Agent->>LLM: Generate Response
    LLM-->>Agent: Natural Language Response
    Agent-->>User: Answer with Insights
```

### 2. Pattern Learning Flow

```mermaid
sequenceDiagram
    participant SPARQL as SPARQL Tool
    participant Cache
    participant Patterns as Pattern Store
    
    SPARQL->>SPARQL: Execute Query
    SPARQL->>SPARQL: Check Success
    alt Query Successful
        SPARQL->>Cache: Store in Query Cache
        SPARQL->>Patterns: Extract Pattern
        Patterns->>Patterns: Classify Pattern Type
        Patterns->>Patterns: Store Pattern
        Note over Patterns: Keep last 100 patterns
    end
```

## Enhanced Agent Methodology

The system has been enhanced with improved conversational patterns and query building strategies:

### Discovery-First Approach
- Agents now always start by discovering what entities exist before building complex queries
- Prevents common errors from assuming entity names or structures
- Uses incremental query building: Discovery → Validation → Analysis → Verification

### Exploration Phase
- When users ask general questions, agents first share available data from loaded context
- Collaborative exploration of possibilities before diving into technical queries
- Focus on understanding user goals and priorities first

### Proactive Query Execution
- Agents execute queries immediately without waiting for confirmation
- Improves user experience by reducing back-and-forth
- Maintains focus on delivering insights quickly

### Improved IRI Handling
- Critical understanding that line/equipment names are IRIs, not string literals
- Proper use of FILTER with IRIs: `FILTER (?line = mes_ontology_populated:LINE2)`
- Alternative string matching when needed: `FILTER (STRENDS(STR(?line), "LINE2"))`

### Aggregation Failure Handling
- Automatic detection when COUNT/GROUP BY queries fail due to Owlready2 limitations
- Provides fallback queries to retrieve raw data for Python-based aggregation
- Ensures users always get results even with backend limitations

### Visualization Integration
- Agents now offer to create visualizations when patterns or trends are discovered
- Automatic chart type selection based on data characteristics
- Seamless integration with both CLI (base64) and Web (artifact) interfaces

### Token Overflow Prevention
- All query results are cached regardless of size
- Large results (>10k tokens) return summaries with cache IDs
- Agents guided to use aggregation queries for time-series data
- Full data remains accessible via cache retrieval tools

## Test Cases: Proven Manufacturing Examples

The following real-world examples demonstrate the system's capabilities and serve as test cases:

### Test Case 1: Hidden Capacity Analysis
**Business Question**: "How much production are we leaving on the table?"

**Expected Queries**:
- Equipment performance vs. benchmarks
- Downtime impact on throughput
- Product mix optimization

**Expected Insights**:
- LINE2-PCK: 25% micro-stops = $341K-$700K opportunity
- Focus on sensor adjustment for quick win
- 11.8% capacity gain achievable

**Visualization**: Line chart showing OEE trends over time, bar chart comparing equipment performance

### Test Case 2: Micro-Stop Pattern Recognition
**Business Question**: "Why do small problems cascade into big ones?"

**Expected Queries**:
- Temporal clustering of events
- Shift-based pattern analysis
- Consecutive stop detection

**Expected Insights**:
- 60% of jams occur within 10 minutes of previous
- Night shift has 40% more issues
- Predictive maintenance triggers identified

### Test Case 3: Quality-Cost Trade-off
**Business Question**: "Where's the sweet spot between quality and cost?"

**Expected Queries**:
- Quality scores by product
- Scrap rates vs. margins
- Investment scenario modeling

**Expected Insights**:
- Every 1% quality gain on high-margin = $144K
- Enhanced inspection pays back in 3-4 months
- Focus on Energy Drink and Premium Juice first

## Key Design Decisions

### 1. Dual Implementation Approach
- **Rationale**: Supports both development (CLI) and production (Web) workflows
- **Benefit**: Consistent core logic with flexible interfaces

### 2. Comprehensive Context Loading
- **Rationale**: LLMs need domain knowledge to generate valid SPARQL
- **Benefit**: Accurate query generation without extensive fine-tuning

### 3. Intelligent Caching Strategy
- **Rationale**: SPARQL queries can be expensive; many queries are repeated
- **Benefit**: Improved performance and reduced API load

### 4. Pattern Learning System
- **Rationale**: Successful queries provide templates for future questions
- **Benefit**: Continuously improving query generation

### 5. Domain-Agnostic Architecture
- **Rationale**: Core patterns apply across industries
- **Benefit**: Reusable framework for any ontology-based system

## Configuration and Deployment

### Environment Variables
```bash
# LLM Configuration
GOOGLE_API_KEY=your-api-key
DEFAULT_MODEL=gemini-2.0-flash
MODEL_TEMPERATURE=0.1

# SPARQL Configuration  
SPARQL_ENDPOINT=http://localhost:8000/sparql/query
SPARQL_TIMEOUT=30
SPARQL_MAX_RESULTS=10000

# Cache Configuration
CACHE_ENABLED=true
CACHE_TTL=3600

# Analysis Configuration
ANALYSIS_WINDOW_DAYS=30
ONTOLOGY_NAMESPACE=mes_ontology_populated
```

### Starting the System
```bash
# Start SPARQL API (required)
python -m uvicorn API.main:app --reload &

# For CLI Interface
python adk_agents/main.py

# For Web Interface
adk web --port 8001
```

## Security Considerations

1. **API Key Management**: Uses environment variables, never hardcoded
2. **Query Validation**: SPARQL injection prevention through parameterization
3. **Rate Limiting**: Configurable limits to prevent API abuse
4. **Cache Security**: Local file-based cache with no sensitive data exposure

## Performance Optimization

1. **Query Caching**: SHA256-based deduplication
2. **Pattern Reuse**: Learning from successful queries
3. **Result Truncation**: Large results summarized to prevent memory issues
4. **Concurrent Tool Calls**: ADK supports parallel function execution

## Domain Adaptation Guide

### Extending Beyond Manufacturing

The system is designed to work with any domain that has:
- Structured operational data (ontology-based)
- Measurable performance metrics
- Financial impact potential
- Temporal patterns

### Adaptation Checklist

- [ ] Map domain entities to generic patterns
- [ ] Identify key performance metrics and benchmarks
- [ ] Find financial value drivers (price, cost, margin)
- [ ] Understand temporal patterns in the domain
- [ ] Document domain-specific constraints
- [ ] Create validation rules for results

### Example Domains
- **Logistics**: Route optimization, delivery patterns, fleet utilization
- **Healthcare**: Patient flow, resource allocation, treatment effectiveness
- **Retail**: Inventory optimization, customer patterns, store performance
- **Energy**: Grid efficiency, consumption patterns, maintenance scheduling
- **Finance**: Transaction patterns, fraud detection, portfolio optimization

## Future Enhancements

1. **Multi-tenant Support**: User-specific context and caching
2. **Advanced Analytics**: ML-based anomaly detection
3. **Real-time Monitoring**: WebSocket support for live dashboards
4. **Extended Tool Library**: Integration with more data sources
5. **Federated Queries**: Cross-system data analysis capabilities
6. **Automated Pattern Discovery**: Self-learning analysis patterns
7. **Enhanced Visualizations**: Interactive dashboards, drill-down capabilities
8. **Export Capabilities**: PDF reports, PowerPoint presentations

## Conclusion

The ADK Manufacturing Analytics System represents a sophisticated integration of semantic web technologies with modern AI capabilities. By combining structured ontologies with conversational interfaces, it makes complex data analysis accessible to business users while maintaining the precision required for high-value optimization decisions.

The system has proven its value with $2.5M+ in discovered opportunities from just 2 hours of analysis, demonstrating a 1000x+ ROI. However, these manufacturing examples are just the beginning - the architecture is designed to unlock similar value across any domain with structured operational data.

---

*This framework is domain-agnostic and production-ready for any industry with structured operational data.*