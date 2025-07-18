# ADK Manufacturing Analytics Agent

A simplified ADK agent system that replicates the Claude Code analytics experience for discovering multi-million dollar opportunities in manufacturing data.

## Overview

This system provides:
- Conversational interface for manufacturing analytics
- Automatic SPARQL query generation from business questions
- Pattern analysis and ROI calculation
- Query caching and learning capabilities

## Setup

1. Copy `.env.example` to `.env` and configure your credentials:
   ```bash
   cp config/.env.example config/.env
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure the SPARQL endpoint is running (default: http://localhost:8000)

4. Run the agent:
   ```bash
   python main.py
   ```

## Architecture

- **Manufacturing Analyst Agent**: Main conversational agent with ontology context
- **SPARQL Tool**: Executes queries with caching and error handling
- **Analysis Tools**: Pattern detection and ROI calculation
- **Context Loader**: Loads ontology and examples for agent context

## Usage

Start a conversation by asking business questions like:
- "What's the OEE performance across our production lines?"
- "Show me quality trends for the last 30 days"
- "Calculate the ROI if we improve Line A's performance to 85%"

The agent will automatically:
1. Convert your question to SPARQL
2. Execute the query
3. Analyze results for patterns
4. Calculate financial impact where relevant