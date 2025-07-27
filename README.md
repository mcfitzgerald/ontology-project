# Ontology-Augmented Manufacturing Analytics System

A comprehensive AI-powered manufacturing analytics platform that bridges structured operational data with conversational AI through semantic ontology modeling. The system has discovered $9.36M in optimization opportunities, demonstrating the power of combining semantic web technologies with modern LLMs for business intelligence.

## Overview

This project implements a complete data-to-insights pipeline that transforms raw manufacturing data into actionable business intelligence through natural language conversations. Built on Google's Agent Development Kit (ADK), the system uses an OWL ontology as a semantic layer between operational data and AI agents, enabling sophisticated analysis without requiring technical expertise from users.

## System Pipeline

```
Data Generation → Ontology Population → SPARQL API → ADK Agent System → Business Insights
```

### Key Features

- **Configurable Data Generation**: Realistic manufacturing data with customizable OEE profiles and business scenarios
- **Semantic Ontology**: OWL-based manufacturing execution system (MES) ontology with TBox/RBox structure
- **SPARQL API**: High-performance RESTful endpoint with Owlready2 integration
- **ADK Analytics Agent**: Conversational AI with discovery-driven methodology and collaborative engagement
- **Pattern Analysis**: Automatic discovery of optimization opportunities worth millions in ROI
- **Smart Caching**: Two-tier cache system preventing token overflow while enabling iterative analysis
- **Progressive Context Loading**: Dynamic context management reducing token usage by 50-70%
- **Dual Interface**: Both CLI and Web UI powered by the same unified agent

## Project Structure

```
ontology-project/
├── Data_Generation/       # Step 1: Manufacturing data generation
│   ├── mes_data_generation.py      # Generates realistic MES data
│   ├── mes_data_config.json        # Configuration for data profiles
│   └── generate_data_catalogue.py  # Creates data inventory
├── Ontology_Generation/   # Step 2: Semantic layer creation
│   ├── mes_ontology_population.py  # Populates ontology from data
│   ├── extract_ontology_to_ttl.py  # Exports to TTL format
│   └── verify_population_completeness.py
├── API/                   # Step 3: SPARQL query service
│   ├── main.py            # FastAPI application
│   ├── sparql_service.py  # Owlready2 SPARQL engine
│   └── docker-compose.yml # Containerization support
├── adk_agents/            # Step 4: Conversational AI agent
│   ├── manufacturing_agent/  # Unified ADK agent
│   ├── tools/             # SPARQL, Python, Cache tools
│   ├── context/           # Dynamic context loader
│   └── main_unified.py    # CLI interface
├── Context/               # Knowledge base and guides
│   ├── system_prompt.md   # Agent behavioral guidelines
│   ├── mes_data_catalogue.json
│   └── owlready2_sparql_lean_reference.md
└── Helper Scripts
    ├── start_services.sh  # Start all services
    ├── check_services.sh  # Health check
    └── stop_services.sh   # Stop services
```

## Installation and Setup

### Prerequisites
- Python 3.9+
- Google API key for Gemini access
- 8GB+ RAM recommended for ontology operations

### Quick Start

```bash
# 1. Clone repository and install dependencies
git clone <repository-url>
cd ontology-project
pip install -r requirements.txt

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY

# 3. Generate manufacturing data (optional - pre-generated data included)
cd Data_Generation
python mes_data_generation.py
python generate_data_catalogue.py
cd ..

# 4. Populate ontology (optional - pre-populated ontology included)
cd Ontology_Generation
python mes_ontology_population.py
cd ..

# 5. Start all services with helper script
./start_services.sh

# Services will be available at:
# - SPARQL API: http://localhost:8000/docs
# - ADK Web UI: http://localhost:8001/dev-ui/
```

### Alternative Manual Start

```bash
# Start SPARQL API
python -m uvicorn API.main:app --reload --port 8000

# In another terminal, start ADK Web UI
adk web --port 8001

# Or use CLI interface
python adk_agents/main_unified.py
```

## Complete System Workflow

### 1. Data Generation Phase
The system starts with configurable manufacturing data generation:

```bash
cd Data_Generation
python mes_data_generation.py
```

This creates:
- 30 days of 5-minute interval production data
- Realistic OEE patterns with shift variations
- Downtime events with business impact
- Quality metrics and scrap rates

### 2. Ontology Population Phase
The semantic layer is created by populating an OWL ontology:

```bash
cd Ontology_Generation
python mes_ontology_population.py
```

This creates:
- TBox (terminology): Equipment types, process classes, KPI definitions
- RBox (relationships): hasEquipment, producedOn, hasDowntime
- ABox (assertions): Individual equipment, production records, events

### 3. SPARQL API Service
The API provides semantic query capabilities:

```bash
python -m uvicorn API.main:app --reload --port 8000
```

Features:
- Owlready2-based SPARQL engine
- Query validation and error hints
- Performance optimization for large datasets
- RESTful endpoints with OpenAPI documentation

### 4. ADK Agent Interaction
The conversational interface enables natural language analysis:

#### Web Interface (Recommended)
```bash
adk web --port 8001
# Navigate to http://localhost:8001/dev-ui/
```

#### CLI Interface
```bash
python adk_agents/main_unified.py
```

### Example Analysis Session

```
You: What equipment has the most improvement potential?

Agent: I'll analyze your manufacturing data to identify equipment with optimization opportunities.
Let me start by exploring what equipment exists and their current performance levels...

[Agent discovers entities, analyzes OEE patterns, identifies bottlenecks]

I've discovered that LINE2-PCK (Packer on Line 2) shows significant improvement potential:
- Current OEE: 68.5% (below world-class 85%)
- Main issue: 81.5 hours of UNP-JAM downtime
- Impact: 342,650 units lost production
- Opportunity: $9.36M annual value if optimized

Would you like me to:
1. Analyze the temporal patterns of these jam events?
2. Compare with other equipment performance?
3. Create a visualization of the opportunity?
```

## Service Management

### Helper Scripts
The project includes bash scripts for easy service management:

```bash
# Start all services (SPARQL API + ADK Web)
./start_services.sh

# Check service status
./check_services.sh

# Stop all services
./stop_services.sh

# Stop and clean logs
./stop_services.sh --clean-logs
```

### Service Architecture
- **SPARQL API (Port 8000)**: Handles ontology queries
  - Health check: http://localhost:8000/health
  - API docs: http://localhost:8000/docs
  
- **ADK Web UI (Port 8001)**: Conversational interface
  - Main UI: http://localhost:8001/dev-ui/
  - Auto-redirects from root URL

## Configuration

### Environment Variables (.env)
```bash
# LLM Configuration
GOOGLE_API_KEY=your-api-key        # Required for ADK agent
DEFAULT_MODEL=gemini-2.0-flash     # Optimized for performance
MODEL_TEMPERATURE=0.1              # Low temperature for consistency

# SPARQL Configuration  
SPARQL_ENDPOINT=http://localhost:8000/sparql/query
SPARQL_TIMEOUT=30                  # Query timeout in seconds
SPARQL_MAX_RESULTS=10000          # Maximum results per query

# Cache Configuration
CACHE_ENABLED=true                 # Enable result caching
CACHE_TTL=3600                    # Cache time-to-live

# Analysis Configuration
ANALYSIS_WINDOW_DAYS=30           # Default analysis period
ONTOLOGY_NAMESPACE=mes_ontology_populated
```

### Data Generation Configuration (mes_data_config.json)
Customize manufacturing scenarios:
- Equipment types and production lines
- Product specifications and margins
- OEE profiles by shift
- Downtime patterns and frequencies
- Quality variations

## Key Design Principles

### 1. Pipeline Architecture
Each component builds on the previous:
- **Data Generation**: Creates realistic manufacturing scenarios
- **Ontology Population**: Adds semantic meaning to raw data
- **SPARQL API**: Provides semantic query interface
- **ADK Agent**: Enables natural language interaction

### 2. Token-Safe Design
- **Two-tier caching**: Query results + full data
- **Smart summarization**: Large results automatically condensed
- **Progressive loading**: Context loaded as needed
- **Result references**: Cache IDs for iterative analysis

### 3. Flexibility Over Prescription
- **Minimal tools**: Just 3 core tools (SPARQL, Python, Cache)
- **Natural discovery**: Patterns emerge through exploration
- **Dynamic context**: Adapts to conversation flow
- **LLM autonomy**: Agent determines best approach

### 4. Business-Driven Analysis
- **ROI focus**: Every insight quantified financially
- **Pattern recognition**: Automatic discovery of opportunities
- **Hypothesis testing**: Iterative exploration approach
- **Actionable insights**: Clear recommendations with value

## Technical Documentation

### Architecture Documentation
For detailed system architecture: [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)

### API Documentation
- SPARQL API: http://localhost:8000/docs (when running)
- ADK Agent: See Context/system_prompt.md for behavioral guidelines

## Proven Business Impact

The system discovered $9.36M in optimization opportunities:

1. **Hidden Capacity**: LINE2-PCK optimization worth $9.36M/year
2. **Micro-Stop Patterns**: Clustering analysis revealing $250K-$350K
3. **Quality Improvements**: Targeted investments worth $200K/year
4. **Shift Performance**: Variations identifying training opportunities

## Domain Adaptation

While demonstrated in manufacturing, the architecture supports any domain with:
- Structured operational data
- Measurable performance metrics
- Financial impact potential
- Temporal patterns

Example domains: Healthcare, Logistics, Retail, Energy, Finance

## Troubleshooting

### Common Issues

1. **Services won't start**: Check ports 8000/8001 aren't in use
   ```bash
   ./stop_services.sh  # Kill any existing services
   ./start_services.sh # Start fresh
   ```

2. **SPARQL timeouts**: Increase SPARQL_TIMEOUT in .env

3. **Token limit errors**: System should auto-cache, but check cache size:
   ```bash
   python -m adk_agents.tools.simple_cache_utils
   ```

4. **Ontology not loading**: Ensure mes_ontology_populated.owl exists:
   ```bash
   ls -la Ontology/
   ```

## License

[Add your license here]

## Contributing

[Add contribution guidelines]

## Acknowledgments

Built on:
- Google Agent Development Kit (ADK)
- Owlready2 for ontology management
- FastAPI for high-performance API
- Gemini 2.0 Flash for conversational AI