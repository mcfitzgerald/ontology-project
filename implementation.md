# ADK Manufacturing Analytics Implementation Plan

## Overview
Create a simplified ADK agent system that replicates the Claude Code analytics experience for discovering multi-million dollar opportunities in manufacturing data.

## Core Architecture
- **One Main Agent**: ManufacturingAnalyst with comprehensive context and tools
- **Optional Sub-Agent**: PythonAnalyst for heavy computational tasks
- **Smart Tools**: SPARQL execution, pattern analysis, ROI calculation
- **State Management**: Shared session state with query caching

## Phase 1: Foundation Setup (Day 1 Morning)

### 1. Create Project Structure
```
/adk_agents/
├── config/
│   ├── __init__.py
│   ├── settings.py (bring from conversational-adk-agents)
│   └── .env.example
├── tools/
│   ├── __init__.py
│   ├── sparql_tool.py
│   ├── analysis_tools.py
│   └── cache_manager.py
├── agents/
│   ├── __init__.py
│   ├── manufacturing_analyst.py
│   └── python_analyst.py (optional)
├── context/
│   ├── __init__.py
│   └── context_loader.py
├── cache/
│   └── .gitkeep
├── main.py
├── requirements.txt
└── README.md
```

### 2. Set Up Configuration
- Copy settings.py from conversational-adk-agents branch
- Create .env file with credentials
- Add ADK-specific configuration settings
- Test authentication (Vertex AI vs API key)

### 3. Install Dependencies
- google-genai
- google-adk
- requests
- python-dotenv
- pandas (for analysis tools)

## Phase 2: Core Tools Implementation (Day 1 Afternoon)

### 1. SPARQL Tool (`tools/sparql_tool.py`)
```python
def execute_sparql(query: str, tool_context: ToolContext) -> dict:
    """Execute SPARQL query with caching and learning"""
```
- Query execution against API endpoint
- Success pattern caching to JSON
- Large result handling with artifacts
- Error handling and retry logic

### 2. Cache Manager (`tools/cache_manager.py`)
- Load/save query patterns
- Pattern classification (capacity, temporal, etc.)
- Usage statistics tracking

### 3. Basic Analysis Tool (`tools/analysis_tools.py`)
```python
def analyze_patterns(data: dict, analysis_type: str, tool_context: ToolContext) -> dict:
    """Perform pattern analysis on query results"""
```
- Temporal pattern detection
- Basic statistics calculation
- Threshold-based insights

## Phase 3: Main Agent Implementation (Day 2 Morning)

### 1. Context Loader (`context/context_loader.py`)
- Load ontology TTL (first 5k chars)
- Load SPARQL reference guide
- Load successful query examples
- Format into concise instruction

### 2. Manufacturing Analyst Agent (`agents/manufacturing_analyst.py`)
```python
analyst = LlmAgent(
    name="ManufacturingAnalyst",
    model="gemini-2.0-flash",
    instruction=comprehensive_context,
    tools=[execute_sparql, analyze_patterns, calculate_roi],
    output_key="current_analysis"
)
```
- Comprehensive instruction with ontology context
- Tool integration
- State management via output_key

### 3. Main Runner (`main.py`)
- Initialize session service
- Create agent and runner
- Interactive conversation loop
- State persistence between queries

## Phase 4: Testing & Refinement (Day 2 Afternoon)

### 1. Test Core Scenarios
- OEE analysis query
- Temporal pattern detection
- Financial impact calculation
- Multi-step analysis flow

### 2. Refine Prompts
- Adjust agent instructions based on behavior
- Optimize context loading
- Fine-tune tool descriptions

### 3. Add ROI Calculation Tool
```python
def calculate_roi(
    current_performance: float,
    target_performance: float,
    annual_volume: float,
    unit_value: float,
    tool_context: ToolContext
) -> dict:
    """Calculate financial impact and ROI"""
```

## Phase 5: Python Sub-Agent (Day 3 - If Needed)

### 1. Python Analyst Agent (`agents/python_analyst.py`)
```python
python_analyst = LlmAgent(
    name="PythonAnalyst",
    model="gemini-2.0-flash",
    instruction="Statistical analysis expert...",
    code_executor=BuiltInCodeExecutor,
    output_key="python_analysis"
)
```

### 2. Integration Options
- As sub_agent for delegation
- As AgentTool for controlled execution
- Conditional routing in main agent

### 3. Test Complex Analyses
- Large dataset processing
- Statistical modeling
- Visualization generation

## Phase 6: Polish & Documentation (Day 3 Afternoon)

### 1. Error Handling
- Graceful SPARQL failures
- Context window management
- Rate limiting implementation

### 2. Documentation
- README with setup instructions
- Example conversations
- Query pattern documentation

### 3. Performance Optimization
- Query result caching
- Context loading optimization
- State cleanup strategies

## Success Criteria

### 1. Functional Requirements
- ✓ Conversational business question → SPARQL → Analysis → ROI
- ✓ Query pattern learning and reuse
- ✓ State persistence across conversation
- ✓ Financial impact quantification

### 2. Quality Metrics
- Response time < 5 seconds for cached queries
- Successful query rate > 80%
- ROI calculations match manual analysis

### 3. Simplicity Goals
- Main implementation < 500 lines of code
- Single agent handles 90% of use cases
- Clear, maintainable structure

## Key Implementation Notes

1. **Start Simple**: Get basic SPARQL tool working first
2. **Test Early**: Validate with known working queries
3. **Iterate on Prompts**: Agent instructions are crucial
4. **Cache Aggressively**: Learn from every success
5. **Fail Gracefully**: Clear error messages, suggest alternatives

## Risk Mitigation

1. **Context Window**: Start with minimal ontology context, expand if needed
2. **Rate Limits**: Built-in throttling from settings.py
3. **Complex Queries**: Fallback to cached patterns
4. **Large Results**: Use artifacts for results > 50KB

This plan prioritizes simplicity while maintaining the power of the original Claude Code experience. The phased approach allows for early testing and iterative refinement.