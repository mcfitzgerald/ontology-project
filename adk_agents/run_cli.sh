#!/bin/bash

# Run the unified Manufacturing Analyst CLI
echo "Starting Manufacturing Analyst CLI..."
echo "==============================="

# Run from the project root to ensure imports work correctly
cd "$(dirname "$0")/.." || exit 1

# Run the unified CLI
python -m adk_agents.main_unified