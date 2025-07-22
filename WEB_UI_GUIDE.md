# Using the Discovery Agent in ADK Web UI

## Access the Web UI

1. Open your browser to: **http://localhost:8001/dev-ui/**
2. You'll see the ADK development interface

## What to Expect

### 1. Discovery-First Approach
The agent will start by exploring what exists before diving into complex analysis:
- "What equipment do you have?"
- "Show me your production lines"
- "What are your main KPIs?"

### 2. Hypothesis-Driven Analysis
Watch as the agent forms and tests hypotheses:
```
🔍 Hypothesis: "Equipment with OEE below 85% likely has optimization opportunities"
📊 Testing: [executes SPARQL query]
💡 Discovery: "LINE2-PCK at 73.2% OEE due to jamming issues"
```

### 3. Financial Quantification
The agent automatically calculates ROI:
- Lost production volume
- Financial impact
- Payback periods
- Implementation priorities

### 4. Pattern Recognition
The agent looks for hidden patterns:
- Temporal clustering (60% of issues within 10 minutes)
- Shift variations (40% worse on night shift)
- Product-specific problems
- Equipment correlations

## Example Queries to Try

### Basic Discovery
- "What equipment exists in the system?"
- "Show me the current performance metrics"
- "What are the main production lines?"

### Optimization Opportunities
- "Find equipment with significant capacity improvement opportunities"
- "Where are we losing the most money?"
- "What's our biggest bottleneck?"

### Pattern Analysis
- "Analyze downtime patterns across shifts"
- "Find temporal clusters in equipment failures"
- "Are there any quality trends by product?"

### Targeted Analysis
- "Why is LINE2-PCK underperforming?"
- "What's causing quality issues on night shift?"
- "How much would reducing micro-stops save?"

## What Makes It Special

1. **No Confirmation Prompts** - The agent executes queries immediately
2. **Progressive Discovery** - Builds knowledge throughout conversation
3. **Quantified Insights** - Every finding includes financial impact
4. **Actionable Recommendations** - Specific steps with expected ROI

## Expected Discoveries

Based on the ontology data, the agent should find:

### Immediate Wins
- **LINE2-PCK Jamming**: $9.36M/year opportunity
- **Hidden micro-stops**: Significant capacity gains
- **Quality variations**: Scrap reduction potential

### Deeper Insights
- Shift performance patterns
- Product-specific equipment issues
- Maintenance correlation opportunities
- Cross-line optimization potential

## Tips for Best Results

1. **Start broad** - Let the agent discover your landscape
2. **Ask "why"** - The agent will dig deeper into root causes
3. **Request comparisons** - "Compare day vs night shift"
4. **Seek patterns** - "Are there any patterns in..."
5. **Quantify everything** - "What's the financial impact?"

## State Persistence

The agent remembers discoveries within a session:
- Previously identified issues
- Calculated benchmarks
- Discovered patterns
- Financial impacts

This allows for progressively deeper analysis as the conversation continues.

## Troubleshooting

If you see warnings about:
- **Token limits**: The agent found too much data - ask for summaries
- **SPARQL errors**: Normal for complex aggregations - agent will retry
- **No results**: Agent will try alternative approaches

The agent is designed to handle these gracefully and find alternative paths to insights!

## Ready to Discover $Millions?

Start with: "What are the biggest opportunities to improve our manufacturing operations?"

The agent will take it from there! 🚀