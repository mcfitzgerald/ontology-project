use context7

# ADK System Startup Instructions
IMPORTANT: This is a Google ADK (Agent Development Kit) project, not just a regular Python project!

To start the system properly:
```bash
# Start SPARQL API in background (port 8000)
python -m uvicorn API.main:app --reload > sparql_api.log 2>&1 &

# Start ADK Web UI in background (port 8001)
adk web --port 8001 > adk_web.log 2>&1 &

# Access the ADK Dev UI at http://localhost:8001

# Check services are running
curl http://localhost:8000/health  # SPARQL API health check
curl http://localhost:8001/         # ADK Web UI
```

The original Python main.py uses input() which doesn't work in web environments. Use ADK Web UI instead!