# ADK Conversational Analysis System - Implementation Plan

## Overview

This plan outlines the creation of a simplified, powerful ADK agent system that replicates the successful conversational analysis experience we had in Claude Code. The system will combine SPARQL discovery with Python-based analysis and visualization to discover multi-million dollar opportunities in manufacturing data.

## Core Objectives

1. **Natural Conversation Flow**: Partner with the user through exploratory analysis
2. **Progressive Discovery**: Build understanding through actual queries, not assumptions
3. **Advanced Analysis**: Use Python for patterns SPARQL can't handle
4. **Business Value Focus**: Always connect findings to financial impact
5. **Learning System**: Build knowledge from successful patterns

## Architecture

### Two-Agent System

1. **Conversation Orchestrator**
   - Manages the analysis workflow
   - Partners with user through discovery
   - Coordinates between SPARQL and Python analysis
   - Maintains conversational context

2. **SPARQL Executor**  
   - Dedicated query execution
   - Learning from successes/failures
   - Query optimization
   - Result caching

### Supporting Components

1. **Context Loader**
   - Dynamically loads ontology mindmap (TTL)
   - Loads SPARQL master reference
   - Extensible for additional contexts

2. **Query Cache & Learning System**
   - Stores successful query patterns
   - Learns from errors
   - Builds pattern library over time

3. **Python Analysis Tools**
   - Statistical analysis (pandas, numpy)
   - Visualization (matplotlib, plotly)
   - Financial calculations
   - Pattern recognition

## Implementation Steps

### Step 1: Create New Git Branch
```bash
git checkout -b conversational-adk-agents
```

### Step 2: Create Context Loader (`adk_agents/utils/context_loader.py`)

```python
"""
Lightweight context loader for agent system prompts.
Loads ontology structure, SPARQL reference, and learned patterns.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

class ContextLoader:
    """Dynamically loads and manages context for agent prompts."""
    
    def __init__(self, context_dir: Path, ontology_dir: Path):
        self.context_dir = context_dir
        self.ontology_dir = ontology_dir
        self.contexts = {}
        self.load_core_contexts()
    
    def load_core_contexts(self):
        """Load essential context files."""
        # Load full TTL mindmap
        mindmap_file = self.context_dir / "mes_ontology_mindmap.ttl"
        if mindmap_file.exists():
            with open(mindmap_file, 'r') as f:
                self.contexts['ontology_mindmap'] = f.read()
        
        # Load full SPARQL master reference
        sparql_ref_file = self.context_dir / "owlready2_sparql_master_reference.md"
        if sparql_ref_file.exists():
            with open(sparql_ref_file, 'r') as f:
                self.contexts['sparql_reference'] = f.read()
        
        # Load learned patterns if exists
        patterns_file = self.context_dir / "learned_patterns.json"
        if patterns_file.exists():
            with open(patterns_file, 'r') as f:
                self.contexts['learned_patterns'] = json.load(f)
        else:
            self.contexts['learned_patterns'] = {
                "successful_queries": [],
                "error_fixes": {},
                "value_patterns": []
            }
    
    def add_learned_pattern(self, pattern_type: str, pattern: Dict[str, Any]):
        """Add a newly learned pattern."""
        if pattern_type in self.contexts['learned_patterns']:
            self.contexts['learned_patterns'][pattern_type].append(pattern)
            self._save_learned_patterns()
    
    def _save_learned_patterns(self):
        """Persist learned patterns."""
        patterns_file = self.context_dir / "learned_patterns.json"
        with open(patterns_file, 'w') as f:
            json.dump(self.contexts['learned_patterns'], f, indent=2)
    
    def get_full_context(self) -> str:
        """Get complete context for system prompts."""
        return f"""
## Ontology Structure and Business Context
{self.contexts.get('ontology_mindmap', 'Ontology structure not loaded')}

## SPARQL Query Reference and Rules
{self.contexts.get('sparql_reference', 'SPARQL reference not loaded')}

## Learned Patterns and Examples
{json.dumps(self.contexts.get('learned_patterns', {}), indent=2)}
"""
```

### Step 3: Create Query Cache System (`adk_agents/utils/query_cache.py`)

```python
"""
Query caching and learning system.
Stores successful patterns and learns from failures.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

class QueryCache:
    """Learns from query successes and failures."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_file = cache_dir / "query_cache.json"
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load existing cache or create new."""
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {
            "successful_queries": [],
            "failed_queries": [],
            "patterns": {},
            "fixes": {}
        }
    
    def add_success(self, query: str, purpose: str, results: Any, 
                   row_count: int, analysis_type: str = None):
        """Record successful query with metadata."""
        entry = {
            "query": query,
            "purpose": purpose,
            "row_count": row_count,
            "analysis_type": analysis_type,
            "timestamp": datetime.now().isoformat(),
            "pattern": self._extract_pattern(query)
        }
        
        self.cache["successful_queries"].append(entry)
        
        # Update pattern statistics
        pattern = entry["pattern"]
        if pattern not in self.cache["patterns"]:
            self.cache["patterns"][pattern] = {"count": 0, "examples": []}
        
        self.cache["patterns"][pattern]["count"] += 1
        self.cache["patterns"][pattern]["examples"].append({
            "query": query,
            "purpose": purpose,
            "row_count": row_count
        })
        
        self._save_cache()
    
    def add_failure(self, query: str, error: str, fixed_query: Optional[str] = None):
        """Record failed query and potential fix."""
        entry = {
            "query": query,
            "error": error,
            "fixed_query": fixed_query,
            "timestamp": datetime.now().isoformat()
        }
        
        self.cache["failed_queries"].append(entry)
        
        # Learn fix patterns
        if fixed_query and "Unknown prefix" in error:
            self.cache["fixes"]["prefix_errors"] = "Always use mes_ontology_populated:"
        elif fixed_query and "Lexing error" in error:
            self.cache["fixes"]["lexing_errors"] = "Remove angle brackets, use FILTER(ISIRI())"
        
        self._save_cache()
    
    def find_similar_success(self, purpose: str, analysis_type: str = None) -> Optional[Dict]:
        """Find similar successful query by purpose."""
        # Simple keyword matching for now
        # Could use embeddings for better similarity
        keywords = purpose.lower().split()
        
        best_match = None
        best_score = 0
        
        for entry in self.cache["successful_queries"]:
            entry_keywords = entry["purpose"].lower().split()
            score = len(set(keywords) & set(entry_keywords))
            
            if analysis_type and entry.get("analysis_type") == analysis_type:
                score += 2
            
            if score > best_score:
                best_score = score
                best_match = entry
        
        return best_match if best_score > 0 else None
    
    def _extract_pattern(self, query: str) -> str:
        """Extract query pattern for learning."""
        # Simplified pattern extraction
        lines = query.strip().split('\n')
        pattern_parts = []
        
        for line in lines:
            if 'SELECT' in line:
                pattern_parts.append('SELECT')
            elif 'WHERE' in line:
                pattern_parts.append('WHERE')
            elif '?equipment' in line and 'logsEvent' in line:
                pattern_parts.append('equipment->event')
            elif 'GROUP BY' in line:
                pattern_parts.append('GROUP_BY')
            elif 'ORDER BY' in line:
                pattern_parts.append('ORDER_BY')
            elif 'FILTER' in line and 'oee' in line.lower():
                pattern_parts.append('FILTER_OEE')
        
        return '-'.join(pattern_parts)
    
    def _save_cache(self):
        """Persist cache to disk."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "successful_queries": len(self.cache["successful_queries"]),
            "failed_queries": len(self.cache["failed_queries"]),
            "learned_patterns": len(self.cache["patterns"]),
            "known_fixes": len(self.cache["fixes"])
        }
```

### Step 4: Create Python Analysis Tool (`adk_agents/tools/python_analysis.py`)

```python
"""
Python execution tool for advanced analysis and visualization.
"""
import io
import base64
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, Optional
import asyncio
from google.adk.tools import FunctionTool

async def execute_python_analysis(
    code: str,
    data: Optional[Dict[str, Any]] = None,
    purpose: str = "analysis"
) -> Dict[str, Any]:
    """
    Execute Python code for data analysis and visualization.
    
    Args:
        code: Python code to execute
        data: Optional data dict (e.g., SPARQL results as DataFrame)
        purpose: Description of analysis purpose
    
    Returns:
        Dict with results, visualizations, and insights
    """
    # Create execution namespace
    namespace = {
        'pd': pd,
        'np': np,
        'plt': plt,
        'sns': sns,
        'data': data or {}
    }
    
    # Capture outputs
    results = {
        'success': True,
        'purpose': purpose,
        'outputs': [],
        'visualizations': [],
        'insights': []
    }
    
    try:
        # Redirect stdout to capture prints
        from contextlib import redirect_stdout
        stdout_capture = io.StringIO()
        
        with redirect_stdout(stdout_capture):
            # Execute code
            exec(code, namespace)
        
        # Capture text output
        text_output = stdout_capture.getvalue()
        if text_output:
            results['outputs'].append(text_output)
        
        # Check for matplotlib figures
        if plt.get_fignums():
            for fig_num in plt.get_fignums():
                fig = plt.figure(fig_num)
                
                # Save to base64
                buffer = io.BytesIO()
                fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.read()).decode()
                
                results['visualizations'].append({
                    'type': 'matplotlib',
                    'format': 'png',
                    'data': img_base64
                })
                
                plt.close(fig)
        
        # Extract any insights variable if defined
        if 'insights' in namespace:
            results['insights'] = namespace['insights']
        
        # Extract any metrics if defined
        if 'metrics' in namespace:
            results['metrics'] = namespace['metrics']
            
    except Exception as e:
        results['success'] = False
        results['error'] = str(e)
        results['error_type'] = type(e).__name__
    
    return results

# Create ADK tool
python_analysis_tool = FunctionTool(
    execute_python_analysis,
    description="Execute Python code for data analysis, statistical calculations, and visualization"
)
```

### Step 5: Create Conversation Orchestrator (`adk_agents/agents/conversation_orchestrator.py`)

```python
"""
Conversation Orchestrator Agent - Partners with user through analysis journey.
"""
from typing import Dict, Any
from pathlib import Path
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from ..utils.context_loader import ContextLoader
from ..utils.query_cache import QueryCache
from ..config.settings import DEFAULT_MODEL, CONTEXT_DIR, ONTOLOGY_DIR

class ConversationOrchestrator:
    """Manages conversational analysis workflow."""
    
    def __init__(self):
        self.context_loader = ContextLoader(CONTEXT_DIR, ONTOLOGY_DIR)
        self.cache = QueryCache(CONTEXT_DIR)
        self.analysis_state = {
            'phase': 'discovery',
            'findings': [],
            'current_focus': None,
            'value_opportunities': []
        }
    
    def get_system_prompt(self) -> str:
        """Build the comprehensive system prompt."""
        cache_stats = self.cache.get_stats()
        
        return f"""
You are a manufacturing analytics expert partnering with the user to discover multi-million dollar opportunities through conversational data exploration.

## Your Role
- You're not just answering questions - you're on a discovery journey together
- Share your thinking process: "Let me explore...", "I'm curious about...", "This is interesting because..."
- Build understanding progressively - don't assume, discover
- Always connect findings to business value

## Analysis Workflow

### Phase 1: Discovery & Understanding
When user asks about data or opportunities:
1. Express curiosity: "Let me explore what data we have about [topic]..."
2. Start with discovery queries to understand what's available
3. Share interesting findings as you discover them
4. Build context together: "I see we have X equipment with Y types of data..."

### Phase 2: Pattern Recognition  
Once we understand the data:
1. Look for anomalies: "I notice that [equipment] has [pattern]..."
2. Ask clarifying questions: "Should we dig deeper into [finding]?"
3. Use SPARQL for data extraction, then Python for advanced analysis
4. Share visualizations: "Here's what the pattern looks like..."

### Phase 3: Quantification & Impact
When patterns emerge:
1. Calculate business impact: "This represents X units/hour lost..."
2. Convert to dollars: "At your margins, that's $Y per year..."
3. Provide scenarios: "If we improve by 25%, that's $Z in savings..."
4. Compare to benchmarks: "Best-in-class achieves 85% OEE..."

### Phase 4: Recommendations
Conclude with actionable insights:
1. Prioritize by ROI: "The biggest opportunity is..."
2. Suggest quick wins vs strategic improvements
3. Provide clear next steps

## Communication Style
- Be conversational: "Let's see what...", "I'm going to check..."
- Celebrate discoveries: "Oh, this is interesting!"
- Think out loud: "I wonder if this correlates with..."
- Ask for guidance: "Would you like to explore X or Y next?"

## Technical Approach

### For SPARQL Queries:
- Delegate to SPARQL Executor with clear purpose
- Start simple, build complexity based on results
- Share what you're looking for and why

### For Python Analysis:
When SPARQL gives us data, use Python for:
- Time series analysis and trend detection
- Statistical calculations (correlations, distributions)
- Visualizations (line plots, heatmaps, pareto charts)
- Financial modeling and scenarios

Example Python patterns:
```python
# Convert SPARQL results to DataFrame
df = pd.DataFrame(data['results'])

# Time series analysis
df['timestamp'] = pd.to_datetime(df['timestamp'])
hourly_avg = df.groupby(df['timestamp'].dt.hour)['oee'].mean()

# Find patterns
micro_stops = df[df['downtime_minutes'].between(1, 5)]
clusters = identify_clusters(micro_stops)

# Calculate impact
capacity_loss = (benchmark_oee - actual_oee) * production_rate
annual_value = capacity_loss * hours_per_year * margin

# Visualize
plt.figure(figsize=(12, 6))
plt.plot(df['timestamp'], df['oee'], alpha=0.7)
plt.axhline(y=85, color='r', linestyle='--', label='Benchmark')
plt.title('OEE Trend with Benchmark')
```

## Current Knowledge Base
- Successful queries cached: {cache_stats['successful_queries']}
- Learned patterns: {cache_stats['learned_patterns']}
- Known error fixes: {cache_stats['known_fixes']}

## Full Technical Context
{self.context_loader.get_full_context()}

Remember: You're a partner in discovery, not just a query executor. Make it feel like we're exploring together!
"""
    
    def create_agent(self, sparql_executor: LlmAgent, python_tool: FunctionTool) -> LlmAgent:
        """Create the orchestrator agent."""
        return LlmAgent(
            name="ConversationOrchestrator",
            model=DEFAULT_MODEL,
            instruction=self.get_system_prompt(),
            description="Partners with user through exploratory manufacturing analysis",
            sub_agents=[sparql_executor],  # Can delegate to SPARQL executor
            tools=[python_tool],  # Direct access to Python analysis
            temperature=0.7  # Slightly higher for conversational tone
        )
```

### Step 6: Create SPARQL Executor (`adk_agents/agents/sparql_executor.py`)

```python
"""
SPARQL Executor Agent - Dedicated query execution with learning.
"""
from typing import Dict, Any, List
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from ..utils.context_loader import ContextLoader
from ..utils.query_cache import QueryCache
from ..config.settings import DEFAULT_MODEL, CONTEXT_DIR, ONTOLOGY_DIR

class SPARQLExecutor:
    """Handles SPARQL query execution and optimization."""
    
    def __init__(self, context_loader: ContextLoader, cache: QueryCache):
        self.context_loader = context_loader
        self.cache = cache
    
    def get_system_prompt(self) -> str:
        """Build SPARQL-focused prompt."""
        return f"""
You are a SPARQL query expert for the MES ontology using Owlready2.

## Your Role
- Execute SPARQL queries requested by the Conversation Orchestrator
- Learn from successes and failures
- Optimize queries for performance
- Handle errors gracefully

## Query Execution Process

1. **Understand the Request**
   - What data is needed and why
   - What analysis will be performed on results

2. **Check Cache First**
   - Look for similar successful queries
   - Reuse patterns that work

3. **Build Query**
   - Start simple if exploring
   - Use known working patterns
   - Apply Owlready2 rules strictly

4. **Execute and Learn**
   - If successful, cache the pattern
   - If failed, diagnose and fix
   - Record lessons learned

## Critical Owlready2 Rules
- ALWAYS use mes_ontology_populated: prefix
- NO angle brackets in queries
- NO PREFIX declarations
- Use FILTER(ISIRI()) for entities
- Timestamps are literals, not IRIs

## Query Patterns That Work

### Discovery Pattern
```sparql
SELECT DISTINCT ?class WHERE {{
    ?class a owl:Class .
    FILTER(ISIRI(?class))
}}
```

### Equipment Performance
```sparql
SELECT ?equipment ?oee ?timestamp WHERE {{
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event a mes_ontology_populated:ProductionLog .
    ?event mes_ontology_populated:hasOEEScore ?oee .
    ?event mes_ontology_populated:hasTimestamp ?timestamp .
    FILTER(ISIRI(?equipment))
}}
ORDER BY ?timestamp
```

### Aggregation Pattern
```sparql
SELECT ?equipment (AVG(?oee) AS ?avgOEE) (COUNT(?event) AS ?count) WHERE {{
    ?equipment mes_ontology_populated:logsEvent ?event .
    ?event mes_ontology_populated:hasOEEScore ?oee .
    FILTER(ISIRI(?equipment))
}}
GROUP BY ?equipment
ORDER BY ?avgOEE
```

## Error Recovery
- "Unknown prefix" → Add mes_ontology_populated:
- "Lexing error" → Remove angle brackets
- "No results" → Check class/property names
- Timeout → Add LIMIT, optimize pattern

## Full Technical Context
{self.context_loader.get_full_context()}

Always explain what you're querying and why. If a query fails, explain what you're trying next.
"""
    
    def create_agent(self, sparql_tool: FunctionTool) -> LlmAgent:
        """Create the SPARQL executor agent."""
        return LlmAgent(
            name="SPARQLExecutor",
            model=DEFAULT_MODEL,
            instruction=self.get_system_prompt(),
            description="Executes SPARQL queries with learning and optimization",
            tools=[sparql_tool],
            temperature=0.1  # Low temperature for consistency
        )
```

### Step 7: Update Main App (`adk_agents/app.py`)

```python
"""
Simplified ADK agent application with conversational analysis.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from adk_agents.utils.context_loader import ContextLoader
from adk_agents.utils.query_cache import QueryCache
from adk_agents.agents.conversation_orchestrator import ConversationOrchestrator
from adk_agents.agents.sparql_executor import SPARQLExecutor
from adk_agents.tools.sparql_tool import execute_sparql_query
from adk_agents.tools.python_analysis import python_analysis_tool
from adk_agents.config.settings import CONTEXT_DIR, ONTOLOGY_DIR

# Initialize shared components
context_loader = ContextLoader(CONTEXT_DIR, ONTOLOGY_DIR)
query_cache = QueryCache(CONTEXT_DIR)

# Create SPARQL tool
sparql_tool = FunctionTool(
    execute_sparql_query,
    description="Execute SPARQL queries against the MES ontology"
)

# Create agents
sparql_executor_instance = SPARQLExecutor(context_loader, query_cache)
sparql_executor = sparql_executor_instance.create_agent(sparql_tool)

orchestrator_instance = ConversationOrchestrator()
orchestrator = orchestrator_instance.create_agent(sparql_executor, python_analysis_tool)

# Export the main agent
root_agent = orchestrator

print(f"✅ Conversational Analysis System initialized")
print(f"   - Context loaded: TTL mindmap and SPARQL reference")
print(f"   - Query cache: {query_cache.get_stats()}")
print(f"   - Ready for exploratory analysis!")
```

### Step 8: Enhanced SPARQL Tool with Learning (`adk_agents/tools/sparql_tool.py`)

Update the existing SPARQL tool to integrate with the cache:

```python
# Add to existing execute_sparql_query function:

from ..utils.query_cache import QueryCache
from ..config.settings import CONTEXT_DIR

# Initialize cache
cache = QueryCache(CONTEXT_DIR)

async def execute_sparql_query(
    query: str,
    parameters: Optional[List[str]] = None,
    timeout: int = SPARQL_TIMEOUT,
    adapt_for_owlready2: bool = True,
    purpose: str = None,
    analysis_type: str = None
) -> Dict[str, Any]:
    """Enhanced SPARQL execution with learning."""
    
    try:
        # Check cache for similar query
        if purpose:
            similar = cache.find_similar_success(purpose, analysis_type)
            if similar:
                print(f"Found similar query pattern: {similar['pattern']}")
        
        # Execute query (existing code)
        # ... 
        
        if response.status == 200:
            # ... existing success handling ...
            
            # Add to cache
            if purpose and results:
                cache.add_success(
                    query=adapted_query,
                    purpose=purpose,
                    results=results,
                    row_count=len(results),
                    analysis_type=analysis_type
                )
            
            return {
                "success": True,
                "results": formatted_results,
                "query": adapted_query,
                "row_count": len(formatted_results),
                "cached": False
            }
        else:
            # ... existing error handling ...
            
            # Record failure
            cache.add_failure(query, error_text)
            
            # Attempt common fixes
            if "Unknown prefix" in error_text:
                fixed_query = query.replace("mes:", "mes_ontology_populated:")
                return await execute_sparql_query(
                    fixed_query, parameters, timeout, 
                    adapt_for_owlready2, purpose, analysis_type
                )
```

## Testing Strategy

### Test Conversation 1: Basic Discovery
```
User: "What data do we have?"
Expected: Orchestrator explores classes, equipment, and available metrics
```

### Test Conversation 2: OEE Analysis
```
User: "Let's explore OEE opportunities"
Expected: 
- Discovery of OEE data
- Identification of underperforming equipment
- Python analysis with visualizations
- Business value calculations
```

### Test Conversation 3: Pattern Recognition
```
User: "Are there any patterns in downtime?"
Expected:
- SPARQL extraction of downtime data
- Python temporal analysis
- Clustering visualization
- ROI calculations for addressing patterns
```

## Benefits of This Approach

1. **Full Context Usage**: Complete TTL and SPARQL reference available
2. **Conversational Flow**: Natural partnership experience
3. **Progressive Learning**: Builds knowledge over time
4. **Powerful Analysis**: SPARQL + Python for complete insights
5. **Business Focus**: Always connects to value
6. **Extensible**: Easy to add new contexts and capabilities

## Next Steps

1. Implement the components
2. Test with simple queries
3. Progress to complex analysis
4. Refine conversational tone
5. Add more Python analysis patterns
6. Build library of successful analyses

This system recreates and enhances the successful Claude Code experience while adding persistent learning and advanced visualization capabilities.