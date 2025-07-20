#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================="
echo "Starting Manufacturing Analytics Services"
echo "========================================="

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo -n "Waiting for $service_name to be ready"
    while [ $attempt -le $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|302"; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done
    echo -e " ${RED}✗ Timeout${NC}"
    return 1
}

# Check if services are already running
echo -e "${YELLOW}Checking current status...${NC}"
if check_port 8000; then
    echo -e "${YELLOW}⚠ SPARQL API already running on port 8000${NC}"
    echo "Run ./stop_services.sh first to stop existing services"
    exit 1
fi

if check_port 8001; then
    echo -e "${YELLOW}⚠ ADK Web UI already running on port 8001${NC}"
    echo "Run ./stop_services.sh first to stop existing services"
    exit 1
fi

# Create log directory if it doesn't exist
mkdir -p logs

# Start SPARQL API
echo -e "\n${BLUE}Starting SPARQL API...${NC}"
echo "Command: python -m uvicorn API.main:app --reload --port 8000"

# Start in background and capture PID
nohup python -m uvicorn API.main:app --reload --port 8000 > sparql_api.log 2>&1 &
SPARQL_PID=$!

echo "SPARQL API started with PID: $SPARQL_PID"
echo "Log file: sparql_api.log"

# Wait for SPARQL API to be ready
wait_for_service "http://localhost:8000/health" "SPARQL API"
SPARQL_READY=$?

# Start ADK Web UI
echo -e "\n${BLUE}Starting ADK Web UI...${NC}"
echo "Command: adk web --port 8001"

# Start in background and capture PID
nohup adk web --port 8001 > adk_web.log 2>&1 &
ADK_PID=$!

echo "ADK Web UI started with PID: $ADK_PID"
echo "Log file: adk_web.log"

# Wait for ADK Web to be ready
wait_for_service "http://localhost:8001/" "ADK Web UI"
ADK_READY=$?

# Display status
echo -e "\n========================================="
echo -e "${YELLOW}Service Status:${NC}"
echo "========================================="

if [ $SPARQL_READY -eq 0 ]; then
    echo -e "SPARQL API: ${GREEN}✓ Running${NC}"
    echo "  └─ URL: http://localhost:8000"
    echo "  └─ Health: http://localhost:8000/health"
    echo "  └─ Docs: http://localhost:8000/docs"
else
    echo -e "SPARQL API: ${RED}✗ Failed to start${NC}"
    echo "  └─ Check sparql_api.log for errors"
fi

if [ $ADK_READY -eq 0 ]; then
    echo -e "ADK Web UI: ${GREEN}✓ Running${NC}"
    echo "  └─ URL: http://localhost:8001"
else
    echo -e "ADK Web UI: ${RED}✗ Failed to start${NC}"
    echo "  └─ Check adk_web.log for errors"
fi

# Save PIDs to file for later reference
echo "SPARQL_PID=$SPARQL_PID" > .service_pids
echo "ADK_PID=$ADK_PID" >> .service_pids

# Show how to monitor logs
echo -e "\n${YELLOW}Monitoring:${NC}"
echo "To monitor SPARQL API logs: tail -f sparql_api.log"
echo "To monitor ADK Web logs: tail -f adk_web.log"
echo "To check status: ./check_services.sh"
echo "To stop services: ./stop_services.sh"

# Final status
if [ $SPARQL_READY -eq 0 ] && [ $ADK_READY -eq 0 ]; then
    echo -e "\n${GREEN}✓ All services started successfully!${NC}"
    echo -e "\n${BLUE}You can now access the ADK Web UI at: http://localhost:8001${NC}"
    exit 0
else
    echo -e "\n${RED}✗ Some services failed to start${NC}"
    exit 1
fi