# Ontology Project - Manufacturing Analytics Platform

A comprehensive manufacturing analytics system that combines semantic ontology modeling with conversational AI to discover multi-million dollar optimization opportunities in manufacturing data.

## Overview

This project provides an intelligent manufacturing analytics platform that has already discovered $2.5M+ in optimization opportunities through just 2 hours of analysis. The system bridges semantic web technologies with modern LLMs to make complex data analysis accessible through natural language conversations.

## Key Features

- **Semantic Ontology**: OWL-based manufacturing execution system (MES) ontology with rich domain modeling
- **SPARQL API**: RESTful endpoint for querying manufacturing data with intelligent caching
- **ADK Analytics Agent**: Conversational AI agent for business intelligence with discovery-first methodology
- **Pattern Analysis**: Automatic discovery of optimization opportunities across temporal, capacity, and quality dimensions
- **Data Visualization**: Generate charts and graphs from query results (line, bar, scatter, pie charts)
- **ROI Calculation**: Financial modeling to quantify improvement opportunities
- **Token-Safe Architecture**: Prevents LLM token overflow by caching large results and returning summaries
- **Dual Interface**: Both CLI and Web UI for different use cases

## Architecture

```
ontology-project/
├── Ontology/              # OWL ontology definitions
│   ├── mes_ontology.ttl
│   └── mes_ontology_populated.owl
├── API/                   # SPARQL query endpoint
│   ├── main.py
│   └── sparql_service.py
├── adk_agents/            # ADK conversational agent
│   ├── agents/            # Agent implementations
│   ├── tools/             # Analysis, SPARQL, visualization, and caching tools
│   ├── context/           # Context loading system
│   └── config/            # Configuration management
└── Context/               # Reference guides and examples
```

## Quick Start

```bash
# 1. Set up environment variables
cp .env.example .env
# Edit .env with your Google API key

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start SPARQL API in background (port 8000)
python -m uvicorn API.main:app --reload > sparql_api.log 2>&1 &

# 4. For Web Interface - Start ADK Web UI (port 8001)
adk web --port 8001 > adk_web.log 2>&1 &

# 5. For CLI Interface - Run the CLI agent
python adk_agents/main.py

# Check services are running
curl http://localhost:8000/health  # SPARQL API health check
curl http://localhost:8001/        # ADK Web UI (if using web interface)
```

## Example Usage

### Web Interface (ADK UI)
Navigate to http://localhost:8001 and start asking questions:
- "What equipment is performing below 70% OEE?"
- "Show me quality trends for the last 30 days"
- "Visualize the OEE performance across all production lines"
- "Calculate ROI if we improve LINE2 to 85% OEE"

### CLI Interface
```bash
$ python adk_agents/main.py

You: What's our biggest optimization opportunity?

Agent: Let me analyze your manufacturing data to identify optimization opportunities...
[Discovers entities, runs queries, analyzes patterns]
I found that LINE2-PCK has 25% micro-stops causing $341K-$700K annual loss.
Would you like me to create a visualization showing the performance trends?

You: Yes, create a line chart of OEE trends for LINE2

Agent: Creating visualization...
[Generates chart showing OEE performance over time]
```

## Visualization Capabilities

The system can create various types of visualizations from your manufacturing data:

- **Line Charts**: Track metrics over time (OEE trends, performance patterns)
- **Bar Charts**: Compare performance across equipment or products
- **Scatter Plots**: Identify correlations (quality vs speed relationships)
- **Pie Charts**: Show distributions (downtime reasons, product mix)

Visualizations are:
- Automatically suggested when patterns are discovered
- Saved as artifacts in the ADK Web UI
- Returned as base64-encoded images in the CLI

## Configuration

### Environment Variables
```bash
# LLM Configuration
GOOGLE_API_KEY=your-api-key        # Required
DEFAULT_MODEL=gemini-2.0-flash     # Optional
MODEL_TEMPERATURE=0.1              # Optional

# SPARQL Configuration  
SPARQL_ENDPOINT=http://localhost:8000/sparql/query
SPARQL_TIMEOUT=30

# Cache Configuration
CACHE_ENABLED=true
CACHE_TTL=3600
```

### Agent Behavior
The agent uses an enhanced methodology:
- **Discovery-First**: Always explores what data exists before complex queries
- **Collaborative**: Engages in dialogue to understand your goals
- **Incremental**: Builds queries step-by-step with validation
- **Visual**: Offers charts and graphs to make insights accessible
- **Token-Safe**: Automatically handles large results by caching and summarization
- **Aggregation-First**: Guides users to use aggregated queries for time-series data

## Development

### Project Structure
- `adk_agents/agents/`: Agent implementations (CLI and ADK Web)
- `adk_agents/tools/`: SPARQL execution, analysis, visualization, and result caching tools
- `adk_agents/context/`: Context loading system with ontology knowledge
- `API/`: SPARQL endpoint with Owlready2 integration

### Key Architectural Features
- **Token Overflow Prevention**: Large query results are automatically cached and summarized
- **Result Cache Manager**: All results cached with UUID-based retrieval system
- **Smart Summaries**: Include sample data, statistics, and metadata for analysis
- **Aggregation Guidance**: Agents trained to use efficient queries for time-series data

### Adding New Capabilities
1. Add new tools in `adk_agents/tools/`
2. Register tools in both agent implementations
3. Update context if new domain knowledge is needed
4. Add test cases to validate functionality

### Testing
```bash
# Test with minimal context (faster)
python adk_agents/main.py --minimal

# Run specific test queries
python -m pytest tests/
```

## Architecture Documentation

For detailed technical documentation, see [adk_agents/SYSTEM_ARCHITECTURE.md](adk_agents/SYSTEM_ARCHITECTURE.md)

## Business Value

This system has proven its value by discovering:
- Hidden capacity worth $341K-$700K/year
- Micro-stop patterns revealing $250K-$350K opportunity  
- Quality improvements worth $200K/year

The architecture is domain-agnostic and can be adapted to any industry with structured operational data.

## License

[Add your license here]

## Contributing

[Add contribution guidelines]