#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "Checking Manufacturing Analytics Services"
echo "========================================="

# Check SPARQL API (port 8000)
echo -n "SPARQL API (port 8000): "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200"; then
    echo -e "${GREEN}✓ Running${NC}"
    # Get PID
    SPARQL_PID=$(lsof -ti:8000)
    if [ ! -z "$SPARQL_PID" ]; then
        echo "  └─ PID: $SPARQL_PID"
    fi
else
    echo -e "${RED}✗ Not running${NC}"
fi

# Check ADK Web UI (port 8001)
echo -n "ADK Web UI (port 8001): "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/ | grep -q "200\|302"; then
    echo -e "${GREEN}✓ Running${NC}"
    # Get PID
    ADK_PID=$(lsof -ti:8001)
    if [ ! -z "$ADK_PID" ]; then
        echo "  └─ PID: $ADK_PID"
    fi
else
    echo -e "${RED}✗ Not running${NC}"
fi

echo "========================================="

# Check for log files
echo -e "\n${YELLOW}Log files:${NC}"
if [ -f "sparql_api.log" ]; then
    echo "SPARQL API log: sparql_api.log ($(wc -l < sparql_api.log) lines)"
    echo "  └─ Last entry: $(tail -1 sparql_api.log | cut -c1-80)..."
fi

if [ -f "adk_web.log" ]; then
    echo "ADK Web log: adk_web.log ($(wc -l < adk_web.log) lines)"
    echo "  └─ Last entry: $(tail -1 adk_web.log | cut -c1-80)..."
fi

# Summary
echo -e "\n${YELLOW}Summary:${NC}"
SPARQL_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
ADK_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/)

if [[ "$SPARQL_STATUS" == "200" ]] && [[ "$ADK_STATUS" == "200" || "$ADK_STATUS" == "302" ]]; then
    echo -e "${GREEN}All services are running properly!${NC}"
    exit 0
else
    echo -e "${RED}Some services are not running.${NC}"
    echo "Run ./start_services.sh to start them."
    exit 1
fi