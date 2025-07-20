# Service Management Scripts

Three bash scripts for managing the Manufacturing Analytics services:

## 1. Check Services Status

```bash
./check_services.sh
```

**Features:**
- Checks if SPARQL API (port 8000) is running
- Checks if ADK Web UI (port 8001) is running
- Shows process IDs (PIDs) for running services
- Displays log file information
- Returns exit code 0 if all services are running, 1 otherwise

## 2. Stop Services

```bash
./stop_services.sh [--clean-logs]
```

**Features:**
- Stops SPARQL API on port 8000
- Stops ADK Web UI on port 8001
- Kills processes by port and by name as backup
- Optional `--clean-logs` flag removes log files
- Verifies all services are stopped

## 3. Start Services

```bash
./start_services.sh
```

**Features:**
- Checks if ports are already in use
- Starts SPARQL API with uvicorn on port 8000
- Starts ADK Web UI on port 8001
- Creates log files (sparql_api.log and adk_web.log)
- Waits for services to be ready (with timeout)
- Saves PIDs to `.service_pids` file
- Shows URLs and monitoring commands

## Usage Examples

### Full restart:
```bash
./stop_services.sh
./start_services.sh
```

### Check status:
```bash
./check_services.sh
```

### Clean restart with log cleanup:
```bash
./stop_services.sh --clean-logs
./start_services.sh
```

### Monitor logs after starting:
```bash
# In one terminal
tail -f sparql_api.log

# In another terminal
tail -f adk_web.log
```

## Service URLs

- **SPARQL API**: http://localhost:8000
  - Health check: http://localhost:8000/health
  - API docs: http://localhost:8000/docs
  
- **ADK Web UI**: http://localhost:8001

## Troubleshooting

If services fail to start:
1. Check if ports are already in use: `lsof -i :8000` or `lsof -i :8001`
2. Check Python environment is activated
3. Check log files for error messages
4. Ensure all dependencies are installed
5. Try running commands manually to see detailed errors