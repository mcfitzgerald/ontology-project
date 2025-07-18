# Google ADK 2025 Import Patterns

## What Changed in ADK 2025

The Google Agent Development Kit (ADK) has significantly evolved in 2025. The key changes are:

### 1. No Direct Runner/SessionService/ArtifactService Imports

**Old Pattern (Pre-2025):**
```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService

# Manual setup
session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()
runner = Runner(agent=my_agent, session_service=session_service, ...)
```

**New Pattern (2025):**
```python
from google.adk.agents import Agent, LlmAgent
from google.adk.tools import FunctionTool

# Just define your agent and export as root_agent
root_agent = LlmAgent(
    name="my_agent",
    model="gemini-2.0-flash",
    tools=[...]
)
```

### 2. Required File Structure

Your ADK agent package must follow this structure:

```
adk_agents/
├── __init__.py      # Must import: from . import agent
├── agent.py         # Must export: root_agent = Agent(...)
└── app.py          # Alternative: can define root_agent here
```

### 3. Correct Import Patterns

```python
# Core imports
from google.adk.agents import Agent, LlmAgent, BaseAgent
from google.adk.tools import FunctionTool

# For types (when needed)
from google.genai import types

# Tools
from google.adk.tools import google_search
from google.adk.tools.bigquery import execute_sql
```

### 4. How to Run

Instead of creating Runner instances, use ADK CLI:

```bash
# Web interface (recommended for development)
adk web adk_agents

# CLI mode
adk run adk_agents

# API server mode (for production)
adk api_server adk_agents
```

### 5. Session and Artifact Management

These are now handled automatically by the ADK framework:
- Session persistence
- Artifact storage
- State management
- Tool execution

## Migration Guide

### Step 1: Remove old imports
```python
# Remove these:
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
```

### Step 2: Update agent definition
```python
# Define your agent
root_agent = LlmAgent(
    name="ontology_analyzer",
    model="gemini-2.0-flash",
    instruction="You are an expert at analyzing manufacturing data...",
    tools=[
        FunctionTool(execute_sparql_query),
        FunctionTool(analyze_with_python)
    ]
)
```

### Step 3: Ensure proper exports
```python
# In agent.py or app.py
root_agent = your_configured_agent  # This name is required!

# In __init__.py
from . import agent  # Required for ADK discovery
```

### Step 4: Use ADK CLI
```bash
# From your project root
adk web adk_agents
```

## Common Issues and Solutions

### ModuleNotFoundError: No module named 'google.adk.runners'
**Solution:** Remove the import. Runner is no longer directly accessible.

### ModuleNotFoundError: No module named 'google.adk.sessions'
**Solution:** Remove the import. Session management is automatic.

### ModuleNotFoundError: No module named 'google.adk.artifacts'
**Solution:** Remove the import. Artifact storage is automatic.

### Agent not found when running `adk web`
**Solution:** Ensure you have `root_agent` exported in agent.py and proper __init__.py imports.

## FastAPI Integration (Production)

For production deployments:

```python
from google.adk.cli.fast_api import get_fast_api_app

app = get_fast_api_app(agent_dir="./adk_agents")

# Add custom routes if needed
@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

## Environment Variables

Configure in `.env`:

```env
# For Vertex AI
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-east1

# OR for API Key
GOOGLE_API_KEY=your-api-key
GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

## References

- ADK Python GitHub: https://github.com/google/adk-python
- ADK Documentation: Context7 ID `/google/adk-python`
- Agent Development Kit Docs: Context7 ID `/google/adk-docs`