#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "Stopping Manufacturing Analytics Services"
echo "========================================="

# Function to kill process on a specific port
kill_port_process() {
    local port=$1
    local service_name=$2
    
    echo -n "Stopping $service_name (port $port): "
    
    # Get PID of process using the port
    PID=$(lsof -ti:$port)
    
    if [ ! -z "$PID" ]; then
        # Kill the process
        kill -9 $PID 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Stopped (PID: $PID)${NC}"
            return 0
        else
            echo -e "${RED}✗ Failed to stop (PID: $PID)${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}Already stopped${NC}"
        return 0
    fi
}

# Stop SPARQL API
kill_port_process 8000 "SPARQL API"
SPARQL_RESULT=$?

# Stop ADK Web UI
kill_port_process 8001 "ADK Web UI"
ADK_RESULT=$?

# Also try to kill by process name as backup
echo -e "\n${YELLOW}Cleaning up any remaining processes...${NC}"

# Kill any uvicorn processes (SPARQL API)
UVICORN_PIDS=$(pgrep -f "uvicorn.*API.main:app")
if [ ! -z "$UVICORN_PIDS" ]; then
    echo "Found uvicorn processes: $UVICORN_PIDS"
    kill -9 $UVICORN_PIDS 2>/dev/null
    echo -e "${GREEN}✓ Killed uvicorn processes${NC}"
fi

# Kill any adk web processes
ADK_PIDS=$(pgrep -f "adk web")
if [ ! -z "$ADK_PIDS" ]; then
    echo "Found ADK web processes: $ADK_PIDS"
    kill -9 $ADK_PIDS 2>/dev/null
    echo -e "${GREEN}✓ Killed ADK web processes${NC}"
fi

# Clean up log files if requested
echo -e "\n${YELLOW}Log files:${NC}"
if [ "$1" == "--clean-logs" ]; then
    if [ -f "sparql_api.log" ]; then
        rm sparql_api.log
        echo -e "${GREEN}✓ Removed sparql_api.log${NC}"
    fi
    if [ -f "adk_web.log" ]; then
        rm adk_web.log
        echo -e "${GREEN}✓ Removed adk_web.log${NC}"
    fi
else
    echo "Log files preserved (use --clean-logs to remove)"
fi

# Final check
echo -e "\n${YELLOW}Final check:${NC}"
sleep 1

SPARQL_CHECK=$(lsof -ti:8000)
ADK_CHECK=$(lsof -ti:8001)

if [ -z "$SPARQL_CHECK" ] && [ -z "$ADK_CHECK" ]; then
    echo -e "${GREEN}✓ All services successfully stopped${NC}"
    exit 0
else
    echo -e "${RED}✗ Some services may still be running${NC}"
    [ ! -z "$SPARQL_CHECK" ] && echo "  - Port 8000 still in use (PID: $SPARQL_CHECK)"
    [ ! -z "$ADK_CHECK" ] && echo "  - Port 8001 still in use (PID: $ADK_CHECK)"
    exit 1
fi