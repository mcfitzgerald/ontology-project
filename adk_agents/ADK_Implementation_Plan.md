# ADK-Based Manufacturing Analytics Agent Implementation Plan

## Project Overview
Create a flexible, exploration-driven agent system that can replicate the emergent analytical process demonstrated in the SPARQL examples, enabling dynamic discovery of business insights without predefined analysis modules.

## Directory Structure
```
ontology-project/
├── [existing files and directories]
└── adk_agents/
    ├── .env
    ├── requirements.txt
    ├── README.md
    ├── config/
    │   ├── __init__.py
    │   ├── settings.py
    │   └── prompts/
    │       ├── __init__.py
    │       ├── ontology_explorer_prompts.py
    │       ├── query_builder_prompts.py
    │       └── analysis_prompts.py
    ├── tools/
    │   ├── __init__.py
    │   ├── sparql_tool.py
    │   ├── ontology_explorer_tool.py
    │   ├── data_analysis_tools.py
    │   └── visualization_tools.py
    ├── agents/
    │   ├── __init__.py
    │   ├── orchestrator_agent.py
    │   ├── ontology_explorer_agent.py
    │   ├── query_builder_agent.py
    │   └── data_analysis_agent.py
    ├── utils/
    │   ├── __init__.py
    │   ├── sparql_utils.py
    │   ├── owlready2_adapter.py
    │   └── financial_calculations.py
    ├── examples/
    │   ├── __init__.py
    │   ├── basic_exploration.py
    │   ├── capacity_analysis.py
    │   └── pattern_discovery.py
    └── tests/
        ├── __init__.py
        ├── test_tools.py
        ├── test_agents.py
        └── test_integration.py
```

## Implementation Details

### Phase 1: Foundation Setup

#### 1.1 Environment Configuration (.env)
```env
# LLM Configuration
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Alternative: Direct API Keys
# GOOGLE_API_KEY=your-google-api-key
# GOOGLE_GENAI_USE_VERTEXAI=FALSE

# SPARQL API Configuration
SPARQL_ENDPOINT=http://localhost:8000/sparql/query
SPARQL_TIMEOUT=30000

# Analysis Configuration
DEFAULT_OEE_BENCHMARK=85.0
DEFAULT_ANALYSIS_WINDOW_DAYS=14
```

#### 1.2 Core Dependencies (requirements.txt)
```
google-generativeai>=0.8.0
google-adk>=0.1.0
pandas>=2.0.0
numpy>=1.24.0
requests>=2.31.0
python-dotenv>=1.0.0
pydantic>=2.0.0
matplotlib>=3.7.0
seaborn>=0.12.0
```

#### 1.3 System Prompts Configuration
Create modular prompt templates that incorporate knowledge from the ontology mindmap and SPARQL guides:

**ontology_explorer_prompts.py**:
- Discovery prompts using Context/mes_ontology_mindmap.ttl
- Relationship exploration templates
- Business context extraction patterns

**query_builder_prompts.py**:
- Owlready2-specific SPARQL patterns from owlready2_sparql_master_reference.md
- Incremental query building approach
- Error handling strategies

**analysis_prompts.py**:
- Pattern recognition templates from llm_driven_oee_analysis_guide.md
- Financial modeling frameworks
- Insight generation structures

### Phase 2: Tool Development

#### 2.1 SPARQL Integration Tool (sparql_tool.py)
```python
from google.adk.tools import FunctionTool
from typing import Dict, List, Optional
import requests
from ..utils.owlready2_adapter import adapt_sparql_for_owlready2

async def execute_sparql_query(
    query: str,
    parameters: Optional[List[str]] = None,
    timeout: int = 30000
) -> Dict:
    """
    Execute SPARQL query against the MES ontology.
    Automatically adapts queries for Owlready2 compatibility.
    """
    # Adapt query for Owlready2
    adapted_query = adapt_sparql_for_owlready2(query)
    
    # Execute query
    payload = {
        "query": adapted_query,
        "timeout": timeout
    }
    if parameters:
        payload["parameters"] = parameters
    
    response = requests.post(
        SPARQL_ENDPOINT,
        json=payload
    )
    
    return response.json()

sparql_tool = FunctionTool(
    func=execute_sparql_query,
    name="sparql_query",
    description="Execute SPARQL queries against the manufacturing ontology"
)
```

#### 2.2 Ontology Explorer Tool (ontology_explorer_tool.py)
```python
async def explore_ontology_structure(
    entity_type: Optional[str] = None,
    relationship: Optional[str] = None,
    include_annotations: bool = True
) -> Dict:
    """
    Discover ontology structure, relationships, and business context.
    Uses pre-loaded ontology mindmap for efficient exploration.
    """
    # Implementation leverages mes_ontology_mindmap.ttl
    pass

async def get_business_context(
    entity: str
) -> Dict:
    """
    Extract business context annotations for an entity.
    """
    pass
```

#### 2.3 Data Analysis Tools (data_analysis_tools.py)
```python
async def analyze_temporal_patterns(
    data: pd.DataFrame,
    time_column: str,
    value_columns: List[str],
    group_by: Optional[List[str]] = None
) -> Dict:
    """
    Generic temporal pattern analysis.
    """
    pass

async def calculate_financial_impact(
    metric_data: pd.DataFrame,
    benchmark: float,
    volume_column: str,
    margin_column: str
) -> Dict:
    """
    Calculate ROI and financial impact.
    """
    pass

async def detect_anomalies(
    data: pd.DataFrame,
    method: str = "statistical"
) -> Dict:
    """
    Flexible anomaly detection.
    """
    pass
```

### Phase 3: Agent Implementation

#### 3.1 Orchestrator Agent (orchestrator_agent.py)
```python
from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool

orchestrator = LlmAgent(
    name="ManufacturingAnalystOrchestrator",
    model="gemini-2.0-flash",
    description="Main coordinator for manufacturing analytics conversations",
    instruction="""
    You are the lead manufacturing analyst coordinating an investigation.
    Your role is to:
    1. Understand the user's business question
    2. Maintain conversation context and discovered insights
    3. Delegate exploration and analysis tasks appropriately
    4. Synthesize findings into actionable business recommendations
    
    You have access to specialized agents:
    - OntologyExplorer: Discovers available data and relationships
    - QueryBuilder: Constructs and executes SPARQL queries iteratively
    - DataAnalyst: Performs statistical and financial analysis
    
    Always focus on business value and ROI. Start simple and build complexity
    based on findings. Look for patterns, not just single data points.
    """,
    sub_agents=[ontology_explorer, query_builder, data_analyst],
    output_key="analysis_summary"
)
```

#### 3.2 Ontology Explorer Agent (ontology_explorer_agent.py)
```python
ontology_explorer = LlmAgent(
    name="OntologyExplorer",
    model="gemini-2.0-flash",
    description="Explores ontology structure to understand available data",
    instruction="""
    You are an ontology expert who helps discover what data is available.
    
    Your capabilities:
    1. Explore entity types and their relationships
    2. Understand business context from annotations
    3. Identify relevant metrics and properties
    4. Map business questions to ontology concepts
    
    Use the ontology mindmap knowledge to guide exploration.
    Always explain the business significance of discovered elements.
    """,
    tools=[explore_ontology_tool, get_context_tool],
    output_key="ontology_insights"
)
```

#### 3.3 Query Builder Agent (query_builder_agent.py)
```python
query_builder = LlmAgent(
    name="QueryBuilder",
    model="gemini-2.0-flash",
    description="Iteratively builds and executes SPARQL queries",
    instruction="""
    You are a SPARQL expert specializing in Owlready2 compatibility.
    
    Key rules:
    - NO PREFIX declarations (use automatic prefix)
    - NO angle brackets
    - Use FILTER(ISIRI()) liberally
    - Start simple, add complexity incrementally
    
    Follow the patterns from owlready2_sparql_master_reference.md.
    Build understanding through exploration, not assumptions.
    """,
    tools=[sparql_tool, query_validation_tool],
    output_key="query_results"
)
```

#### 3.4 Data Analysis Agent (data_analysis_agent.py)
```python
data_analyst = LlmAgent(
    name="DataAnalyst",
    model="gemini-2.0-flash",
    description="Performs statistical analysis and financial modeling",
    instruction="""
    You are a data scientist specializing in manufacturing analytics.
    
    Your approach:
    1. Identify patterns in data (temporal, correlational, clustering)
    2. Calculate business impact and ROI
    3. Generate actionable insights with specific recommendations
    4. Validate findings against known business contexts
    
    Always quantify opportunities in financial terms.
    Focus on patterns that lead to actionable improvements.
    """,
    tools=[temporal_analysis_tool, financial_modeling_tool, 
           anomaly_detection_tool, visualization_tool],
    output_key="analysis_findings"
)
```

### Phase 4: Integration Features

#### 4.1 Session Management
```python
from google.adk.session import InMemorySessionService

class AnalysisSessionManager:
    """
    Maintains context across the analytical conversation.
    Tracks discovered insights, query history, and findings.
    """
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.discovered_patterns = []
        self.query_history = []
        self.financial_opportunities = []
```

#### 4.2 Conversation Flow
```python
from google.adk.runner import Runner

class ManufacturingAnalyticsChat:
    """
    Main chat interface for natural conversation flow.
    """
    def __init__(self):
        self.runner = Runner(
            agent=orchestrator,
            app_name="manufacturing_analytics",
            session_service=session_manager
        )
    
    async def analyze(self, user_question: str):
        """
        Process user question through agent pipeline.
        """
        # Implementation handles streaming responses
        pass
```

### Phase 5: Example Implementations

#### 5.1 Basic Exploration (examples/basic_exploration.py)
```python
# Example: "What equipment is performing below benchmark?"
async def explore_underperforming_equipment():
    chat = ManufacturingAnalyticsChat()
    response = await chat.analyze(
        "Which equipment has OEE below 85%? What's the impact?"
    )
```

#### 5.2 Pattern Discovery (examples/pattern_discovery.py)
```python
# Example: "When do problems typically occur?"
async def discover_temporal_patterns():
    chat = ManufacturingAnalyticsChat()
    response = await chat.analyze(
        "Are there patterns in when equipment failures occur?"
    )
```

### Phase 6: Testing Strategy

#### 6.1 Unit Tests
- Test each tool independently
- Validate SPARQL query adaptation
- Test financial calculations

#### 6.2 Integration Tests
- Test agent collaboration
- Validate end-to-end analysis flows
- Ensure proper context maintenance

#### 6.3 Validation Tests
- Recreate the $2.5M opportunity analyses
- Verify flexibility for new questions
- Test error handling and recovery

## Key Design Decisions

1. **Generic Tools**: All analysis tools are parameterized and flexible
2. **Emergent Discovery**: No hardcoded analysis types or patterns
3. **Context Accumulation**: Session state builds understanding over time
4. **Iterative Approach**: Queries and analysis build incrementally
5. **Business Focus**: Every technical finding connects to business value

## Next Steps After Implementation

1. **Deployment**: Package for easy startup alongside existing SPARQL API
2. **Documentation**: Create user guide with example questions
3. **Monitoring**: Track discovered insights and query patterns
4. **Enhancement**: Add real-time data integration capabilities
5. **Scaling**: Consider multi-ontology support for broader applications

## Integration with Existing Resources

### Leveraging Existing Documentation

1. **Ontology Structure** (`Context/mes_ontology_mindmap.ttl`):
   - Pre-loaded for efficient exploration
   - Business context annotations guide analysis
   - Relationship mappings inform query building

2. **SPARQL Compatibility** (`SPARQL_Examples/owlready2_sparql_master_reference.md`):
   - Query adaptation rules built into tools
   - Working patterns as templates
   - Error handling strategies

3. **Analysis Patterns** (`SPARQL_Examples/llm_driven_oee_analysis_guide.md`):
   - Generic framework principles embedded in agent instructions
   - Financial modeling approaches in analysis tools
   - Pattern recognition strategies

4. **LLM Best Practices** (`SPARQL_Examples/owlready2_sparql_llm_guide.md`):
   - Query generation guidelines
   - Business insight patterns
   - Testing approaches

## Subdirectory Implementation Considerations

### Working Within the Ontology Project Repository

The ADK agents are designed to work as a subdirectory within the existing ontology project, providing several advantages:

#### 1. Python Path Management
Since `adk_agents/` needs to reference parent directory files:

```python
# In adk_agents/utils/ontology_loader.py
import os
import sys

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

# Now you can access ontology files
MINDMAP_PATH = os.path.join(parent_dir, "Context", "mes_ontology_mindmap.ttl")
SPARQL_GUIDES_DIR = os.path.join(parent_dir, "SPARQL_Examples")
```

#### 2. Virtual Environment Setup
Create and manage the virtual environment within the subdirectory:

```bash
cd adk_agents
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 3. Running the ADK System
Launch the ADK web interface from the subdirectory:

```bash
cd adk_agents
adk web  # ADK will discover agents in the current directory
```

#### 4. File Access Patterns
Example of accessing parent directory resources:

```python
# In adk_agents/config/settings.py
import os
from pathlib import Path

# Project root detection
ADK_AGENTS_DIR = Path(__file__).parent.parent
PROJECT_ROOT = ADK_AGENTS_DIR.parent

# Resource paths
ONTOLOGY_DIR = PROJECT_ROOT / "Ontology"
CONTEXT_DIR = PROJECT_ROOT / "Context"
SPARQL_EXAMPLES_DIR = PROJECT_ROOT / "SPARQL_Examples"
DATA_DIR = PROJECT_ROOT / "Data"

# Load mindmap for reference
MINDMAP_FILE = CONTEXT_DIR / "mes_ontology_mindmap.ttl"
```

#### 5. Import Structure
Internal imports within adk_agents:

```python
# Within adk_agents files
from tools.sparql_tool import sparql_tool
from agents.orchestrator_agent import orchestrator
from utils.owlready2_adapter import adapt_sparql_for_owlready2
```

#### 6. Docker Considerations (Future)
If containerization is needed:

```dockerfile
# Dockerfile in project root
FROM python:3.9-slim

# Copy entire project
COPY . /app
WORKDIR /app/adk_agents

# Install dependencies
RUN pip install -r requirements.txt

# Run ADK
CMD ["adk", "web"]
```

### Advantages of This Approach

1. **Unified Repository**: Single clone for complete system
2. **Shared Resources**: Direct access to ontology files and documentation
3. **Version Control**: Everything tracked together
4. **Easy Publishing**: Complete solution in one repository
5. **No Duplication**: Reference existing files rather than copying

### Setup Checklist

- [ ] Create `adk_agents/` subdirectory structure
- [ ] Set up virtual environment inside `adk_agents/`
- [ ] Create utility module for parent directory access
- [ ] Configure `.env` with proper paths
- [ ] Test file access from subdirectory
- [ ] Verify ADK can discover agents
- [ ] Test SPARQL API connectivity

## Success Criteria

1. **Flexibility**: Can answer any business question about the manufacturing data
2. **Accuracy**: Generates valid Owlready2-compatible SPARQL queries
3. **Value Discovery**: Identifies opportunities comparable to the $2.5M example
4. **User Experience**: Natural conversation flow with clear insights
5. **Maintainability**: Modular design allows easy enhancement

This implementation provides a foundation for dynamic, exploration-driven analysis that can adapt to any business question while maintaining the rigor and value focus demonstrated in your examples.