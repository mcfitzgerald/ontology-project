# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Manufacturing Execution System (MES) Ontology Analytics Platform that demonstrates how semantic web technologies and AI can discover multi-million dollar opportunities in manufacturing data. The project combines OWL ontologies, SPARQL queries, and Google ADK agents to analyze bottling plant operations.

## Essential Commands

### Setup and Run
```bash
# 1. Generate synthetic manufacturing data
python Data_Generation/mes_data_generation.py

# 2. Populate the ontology with data
python Ontology_Generation/mes_ontology_population.py

# 3. Generate LLM context (TTL mindmap)
python Ontology_Generation/extract_ontology_to_ttl.py

# 4. Start the SPARQL API server
python -m uvicorn API.main:app --reload

# 5. Test SPARQL connectivity
python -m adk_agents.test_simple

# 6. Run interactive demo
python -m adk_agents.examples.demo_analysis
```

### Testing
```bash
# Test API endpoints
python API/test_api.py

# Test ADK agents
python -m adk_agents.test_simple
python -m adk_agents.test_automated
python -m adk_agents.test_cost_monitoring
```

### Docker (for API)
```bash
cd API
docker-compose up --build
```

## Architecture

The system follows a layered architecture:

1. **Data Layer** (`/Data_Generation/`): Generates synthetic manufacturing data with configurable anomalies
2. **Ontology Layer** (`/Ontology_Generation/`): Converts CSV data to OWL ontology using Owlready2
3. **API Layer** (`/API/`): FastAPI server providing SPARQL query endpoint
4. **AI Agent Layer** (`/adk_agents/`): Google ADK agents that orchestrate analysis and discover insights

Key relationships:
- Equipment → produces → Products
- Equipment → generates → Events (alarms, KPIs)
- Orders → contain → Products
- Events track OEE, defect rates, production volumes

## Critical SPARQL Requirements

**ALWAYS use the full prefix `mes_ontology_populated:` in SPARQL queries.**

Correct: `mes_ontology_populated:hasOEEScore`
Wrong: `mes:hasOEEScore` or `:hasOEEScore`

This is due to Owlready2's SPARQL engine requirements.

## Environment Configuration

Configure `/adk_agents/.env` before running agents:

```env
# For Vertex AI (recommended)
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-east1

# OR for API Key
GOOGLE_API_KEY=your-api-key
GOOGLE_GENAI_USE_VERTEXAI=FALSE

# SPARQL endpoint
SPARQL_ENDPOINT=http://localhost:8000/sparql/query
SPARQL_TIMEOUT=30
```

## Key Files to Know

- `/Data_Generation/mes_data_config.json` - Anomaly configuration
- `/Ontology_Generation/Tbox_Rbox.md` - Ontology schema documentation
- `/Context/owlready2_sparql_master_reference.md` - SPARQL query patterns
- `/API/main.py` - FastAPI server implementation
- `/adk_agents/orchestrator.py` - Main agent orchestration logic

## Development Notes

1. The project uses custom test scripts rather than pytest/unittest
2. No linting configuration exists - follow existing code style
3. Dependencies are in `requirements.txt` (199 packages)
4. Minimum 4GB RAM required for ontology operations
5. API uses thread parallelism for performance
6. All data generation configs are in JSON format

## Security Note

The repository contains an API key in `/adk_agents/.env` that should be removed and regenerated before any commits.