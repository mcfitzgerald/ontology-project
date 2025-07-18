# Ontology Project - Manufacturing Analytics Platform

A comprehensive manufacturing analytics system that combines semantic ontology modeling with conversational AI to discover multi-million dollar optimization opportunities in manufacturing data.

## Overview

This project provides:
- **Semantic Ontology**: OWL-based manufacturing execution system (MES) ontology
- **SPARQL API**: RESTful endpoint for querying manufacturing data
- **ADK Analytics Agent**: Conversational AI agent for business intelligence
- **Pattern Analysis**: Automatic discovery of optimization opportunities

## Architecture

```
ontology-project/
Ontology/              # OWL ontology definitions
API/                   # SPARQL query endpoint
adk_agents/            # ADK conversational agent
Context/               # Reference guides and examples
```

## Quick Start

### 1. Start the SPARQL API Server

```bash
cd API
pip install -r requirements.txt
python main.py
```

The API will start at `http://localhost:8000` with:
- SPARQL endpoint: `/sparql/query`
- Interactive docs: `/docs`

### 2. Run the ADK Analytics Agent

```bash
cd adk_agents
pip install -r requirements.txt

# Configure your Google API key
cp config/.env.example config/.env
# Edit .env and add your GOOGLE_API_KEY

python main.py
```

## Key Features

### Semantic Ontology
- Models equipment, products, orders, and events
- Supports OEE (Overall Equipment Effectiveness) calculations
- Tracks quality metrics and production performance

### Conversational Analytics
Ask natural language questions like:
- "What's the OEE performance across our production lines?"
- "Show me quality trends for the last 30 days"
- "Calculate ROI if we improve Line A's performance to 85%"
- "Which equipment has the most downtime events?"

### Pattern Learning
- Caches successful queries for reuse
- Learns query patterns by type (capacity, quality, temporal)
- Provides similar query suggestions

### Financial Analysis
- Automatic ROI calculations
- 5-year financial projections
- Implementation cost estimates

## Example Analysis Flow

1. **Business Question**: "Find equipment performing below 70% OEE"
2. **SPARQL Generation**: Agent converts to semantic query
3. **Pattern Analysis**: Identifies underperforming equipment
4. **ROI Calculation**: Quantifies improvement opportunity
5. **Recommendations**: Provides actionable insights

## Components

### API Server (`/API`)
- FastAPI-based SPARQL endpoint
- Owlready2 for ontology reasoning
- Configurable query limits and timeouts

### ADK Agent (`/adk_agents`)
- Google Gemini-powered conversational AI
- Tool-based architecture for extensibility
- Session state management

### Context Management (`/Context`)
- SPARQL reference for Owlready2
- Successful query examples
- Data catalogue with equipment inventory

## Configuration

### API Configuration
Create `API/.env`:
```env
# Server settings
API_HOST=0.0.0.0
API_PORT=8000

# Query settings
QUERY_TIMEOUT=60
MAX_QUERY_LENGTH=10000
```

### Agent Configuration
Create `adk_agents/config/.env`:
```env
# LLM settings
USE_VERTEX_AI=false
GOOGLE_API_KEY=your-api-key-here

# SPARQL endpoint
SPARQL_ENDPOINT=http://localhost:8000/sparql/query

# Analysis settings
OEE_BENCHMARK=85.0
```

## Requirements

- Python 3.8+
- Google API key (for Gemini access)
- 4GB RAM minimum
- Modern web browser (for API docs)

## License

This project is proprietary and confidential.

## Support

For issues or questions:
- Check the troubleshooting guide in `/adk_agents/README.md`
- Review example queries in `/API/example_client.py`
- Examine the ontology structure in `/Ontology/mes_ontology_populated.owl`