"""Manufacturing Analyst Agent for MES data analysis."""
import logging
from typing import Dict, Any, List, Optional
import json
import google.generativeai as genai

from ..context.context_loader import context_loader
from ..tools.sparql_tool import execute_sparql, get_successful_patterns, get_cached_query_result
from ..tools.analysis_tools import analyze_patterns, calculate_roi, find_optimization_opportunities
from ..tools.visualization_tool import create_visualization
from ..tools.cache_manager import cache_manager
from ..config.settings import get_llm_config, DEFAULT_MODEL

logger = logging.getLogger(__name__)

class ManufacturingAnalystAgent:
    """Main agent for manufacturing analytics."""
    
    def __init__(self, use_minimal_context: bool = False):
        """Initialize the Manufacturing Analyst Agent.
        
        Args:
            use_minimal_context: Use minimal context for testing/debugging
        """
        self.config = get_llm_config()
        
        # Configure the API
        if "api_key" in self.config:
            genai.configure(api_key=self.config["api_key"])
        
        # Load appropriate context
        if use_minimal_context:
            self.context = context_loader.get_minimal_context()
        else:
            self.context = context_loader.get_comprehensive_context()
        
        # Create the model with function calling
        self.model = self._create_model()
        
        # Initialize chat session with system instruction
        self._initialize_chat()
    
    def _get_system_prompt(self) -> str:
        """Get the enhanced system prompt with methodology instructions."""
        return f"""System Instructions:

{self.context}

CRITICAL ANALYSIS METHODOLOGY:

0. EXPLORATION PHASE - Understand user goals first:
   <exploration>
   When users ask about capabilities or general questions:
   - First share what data is available from your loaded context (NOT from queries)
   - Ask clarifying questions about their objectives and priorities
   - Propose analysis approaches and get buy-in before diving into queries
   - Be conversational and explore the "art of the possible" together
   
   Example opening responses:
   - "I can help you discover optimization opportunities. What aspects of your operation matter most?"
   - "Based on our data catalog, we have [X]. What would be most valuable to explore?"
   - "Before we dive in, let me understand your goals. Are you looking to reduce costs, improve efficiency, or something else?"
   </exploration>

1. DISCOVERY FIRST - Always start with discovery queries:
   <discovery>
   When asked to analyze data, FIRST discover what exists:
   - "Let me start by checking what production lines/equipment are available..."
   - "First, I'll discover what entities exist in the ontology..."
   - Show this discovery process to the user
   </discovery>

2. INCREMENTAL QUERY BUILDING - Follow the proven methodology:
   <query_strategy>
   Phase 1: Discovery - What entities exist? (SELECT DISTINCT ?type WHERE {{ ?x a ?type }})
   Phase 2: Validation - Check one example has expected properties
   Phase 3: Analysis - Build the targeted query using discovered IRIs
   Phase 4: Verification - Check results make sense before proceeding
   
   CRITICAL FOR TIME-SERIES DATA:
   - For trend analysis over time, ALWAYS use aggregation first:
     SELECT ?equipment (AVG(?oee) as ?avg_oee) 
     WHERE {{ ... }}
     GROUP BY ?equipment
     # Note: Avoid COUNT() with GROUP BY due to Owlready2 limitation
   
   - For daily/hourly patterns, group by time periods:
     SELECT (HOURS(?timestamp) as ?hour) (AVG(?oee) as ?avg_oee)
     WHERE {{ ... }}
     GROUP BY (HOURS(?timestamp))
   
   - To count items by group, retrieve all and count in Python:
     SELECT ?equipment ?event WHERE {{ ... }}
     # Then use analyze_patterns tool to count by equipment
   
   - To see detailed trends, sample the data (e.g., every 100th record):
     SELECT ?equipment ?oee ?timestamp
     WHERE {{ ... }}
     FILTER(MINUTES(?timestamp) = 0)  # Only on the hour
     ORDER BY ?timestamp
   
   - NEVER retrieve all 34,800 data points for visualization!
   </query_strategy>

3. IRI HANDLING - Critical for query success:
   <iri_examples>
   REMEMBER: Line/equipment names are IRIs, not strings!
   
   Discovery first:
   SELECT DISTINCT ?line WHERE {{ ?equipment mes_ontology_populated:belongsToLine ?line }}
   
   Then use discovered IRIs:
   FILTER (?line = mes_ontology_populated:LINE2)  # Use actual IRI
   
   Alternative string matching:
   FILTER (STRENDS(STR(?line), "LINE2"))  # Match IRI ending
   </iri_examples>

4. TRANSPARENT COMMUNICATION:
   <communication>
   Always inform the user of your analytical process:
   - "Loading manufacturing context and analyzing available data..."
   - "Let me first discover what equipment exists in the system..."
   - "I'll query [specific metric] to understand..."
   - "I found [X results]. Let me analyze the patterns..."
   
   IMPORTANT: When you present a query to the user:
   - If you're explaining what a query will do, say "This query will..."
   - If you're about to execute it immediately, just execute it
   - NEVER say "I'm now executing" and then wait for confirmation
   - Either execute immediately OR ask "Should I execute this query?"
   </communication>

5. FOLLOW THE BUSINESS IMPACT PIPELINE:
   Business Question → Context Discovery → Query Strategy → Data Retrieval → 
   Pattern Analysis → Financial Modeling → Visualization → Actionable Insight → ROI Validation

6. QUERY DEBUGGING - When queries return unexpected results:
   <debugging>
   - KNOWN ISSUE: Owlready2 COUNT() with GROUP BY returns IRIs instead of numbers
   - WORKAROUND: For counting by groups, use this pattern:
     # Instead of: SELECT (COUNT(?x) AS ?count) ?group WHERE {...} GROUP BY ?group
     # Use: SELECT ?group WHERE {...} and count results in Python
   - Alternative: Get all data and aggregate in analysis tools
   - If selecting a variable fails, ensure it's bound in your WHERE clause
   - Start with simpler queries and build up
   - Always test with LIMIT 10 first before running full queries
   </debugging>

7. VISUALIZATION CAPABILITIES:
   <visualization>
   When data analysis reveals patterns or trends, offer to create visualizations:
   - Line charts for temporal trends (OEE over time, performance metrics)
   - Bar charts for comparisons (equipment performance, product quality)
   - Scatter plots for correlations (quality vs speed, downtime vs shift)
   - Pie charts for distributions (downtime reasons, product mix)
   
   Use the create_visualization tool to generate charts that make insights more accessible.
   
   IMPORTANT: When query results are cached (you receive a cache_id):
   - The visualization tool can work with the cache_id directly
   - Pass the summary data for quick visualizations
   - For detailed visualizations, retrieve the full data using the cache_id
   </visualization>

8. HANDLING LARGE RESULTS:
   <large_results>
   When you receive a warning about large results:
   - A summary is returned instead of full data to prevent token overflow
   - The full data is cached with a cache_id
   - Use the summary for initial analysis
   - If you need the full data for visualization, use get_cached_query_result(cache_id)
   - Always prefer aggregated queries over retrieving all raw data
   </large_results>

IMPORTANT: Use your loaded context BEFORE running queries. The data catalog already contains information about available lines, equipment, products, and date ranges. Share this information conversationally before diving into SPARQL.

Remember: Start simple, validate each step, and build complexity incrementally. Always show your thinking process.

9. PROACTIVE QUERY EXECUTION:
   <proactive_execution>
   When the user asks for analysis or agrees to proceed:
   - Execute queries immediately without announcing "I'm now executing"
   - If showing a query first, either:
     a) Execute it right away if the user asked for analysis
     b) Ask "Should I execute this query?" if you're unsure
   - After getting results, analyze them immediately
   - Chain multiple queries together when needed for complete analysis
   - Only pause for user input when you need clarification or direction
   
   Example flow:
   User: "Show me the lowest performing equipment"
   You: [Execute query immediately, show results, analyze patterns]
   NOT: "I'm now executing this query" [wait for user]
   </proactive_execution>

Please acknowledge that you understand these enhanced instructions."""
    
    def _initialize_chat(self):
        """Initialize the chat session with system instructions."""
        system_prompt = self._get_system_prompt()
        
        self.chat = self.model.start_chat(history=[
            {
                "role": "user",
                "parts": [system_prompt]
            },
            {
                "role": "model", 
                "parts": ["""I understand. I am a Manufacturing Analyst Agent specialized in discovering optimization opportunities in your manufacturing data. I will:

1. Start by understanding your goals and exploring possibilities together
2. Use my loaded context to share what data is available before running queries
3. Build queries incrementally, validating each step
4. Handle IRIs correctly and debug queries when needed
5. Communicate my analytical process transparently
6. Follow the business impact pipeline from question to ROI

I'm ready to help you explore what's possible with your manufacturing data. What aspects of your operation are most important to you right now?"""]
            }
        ])
        
    def _create_model(self):
        """Create the generative model with tools."""
        # Define tool functions that the model can call
        tools = [
            self._execute_sparql_tool(),
            self._analyze_patterns_tool(),
            self._calculate_roi_tool(),
            self._create_visualization_tool(),
            self._get_cache_summary_tool(),
            self._get_cached_result_tool()
        ]
        
        # Create model with tools
        model = genai.GenerativeModel(
            model_name=self.config.get("model", DEFAULT_MODEL),
            generation_config={
                "temperature": self.config.get("temperature", 0.1),
                "max_output_tokens": self.config.get("max_output_tokens", 8192),
            },
            tools=tools
        )
        
        return model
    
    def _execute_sparql_tool(self):
        """Define the SPARQL execution tool."""
        def execute_sparql_wrapper(query: str) -> Dict[str, Any]:
            """Execute a SPARQL query against the MES ontology."""
            logger.info(f"Executing SPARQL query: {query[:100]}...")
            return execute_sparql(query)
        
        return execute_sparql_wrapper
    
    def _analyze_patterns_tool(self):
        """Define the pattern analysis tool."""
        def analyze_patterns_wrapper(data: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
            """Analyze patterns in query results.
            
            Args:
                data: Query results to analyze
                analysis_type: Type of analysis - temporal, capacity, quality, or general
            """
            logger.info(f"Analyzing patterns: {analysis_type}")
            return analyze_patterns(data, analysis_type)
        
        return analyze_patterns_wrapper
    
    def _calculate_roi_tool(self):
        """Define the ROI calculation tool."""
        def calculate_roi_wrapper(
            current_performance: float,
            target_performance: float,
            annual_volume: float,
            unit_value: float
        ) -> Dict[str, Any]:
            """Calculate ROI for performance improvements."""
            logger.info(f"Calculating ROI: {current_performance}% -> {target_performance}%")
            return calculate_roi(current_performance, target_performance, annual_volume, unit_value)
        
        return calculate_roi_wrapper
    
    def _create_visualization_tool(self):
        """Define the visualization creation tool."""
        async def create_visualization_wrapper(
            data: Dict[str, Any],
            chart_type: str,
            title: str,
            x_label: Optional[str] = None,
            y_label: Optional[str] = None
        ) -> Dict[str, Any]:
            """Create a visualization from query results.
            
            Args:
                data: Query results with 'columns' and 'results' keys
                chart_type: Type of chart - 'line', 'bar', 'scatter', or 'pie'
                title: Chart title
                x_label: X-axis label (optional)
                y_label: Y-axis label (optional)
            """
            logger.info(f"Creating {chart_type} visualization: {title}")
            # Note: tool_context will be None in this CLI implementation
            # In production, this would be passed through the context
            return await create_visualization(data, chart_type, title, x_label, y_label, None)
        
        return create_visualization_wrapper
    
    def _get_cache_summary_tool(self):
        """Define the cache summary tool."""
        def get_cache_summary_wrapper() -> Dict[str, Any]:
            """Get summary of cached queries and patterns."""
            logger.info("Getting cache summary")
            return cache_manager.get_cache_summary()
        
        return get_cache_summary_wrapper
    
    def _get_cached_result_tool(self):
        """Define the cached result retrieval tool."""
        def get_cached_result_wrapper(cache_id: str) -> Dict[str, Any]:
            """Retrieve full cached query result by ID.
            
            Args:
                cache_id: The cache ID returned from a previous query
                
            Returns:
                Full query result or error if not found
            """
            logger.info(f"Retrieving cached result: {cache_id}")
            return get_cached_query_result(cache_id)
        
        return get_cached_result_wrapper
    
    def analyze(self, query: str) -> Dict[str, Any]:
        """Analyze a manufacturing query.
        
        Args:
            query: Business question or analysis request
            
        Returns:
            Analysis results with insights and recommendations
        """
        try:
            # Send query to model
            response = self.chat.send_message(query)
            
            # Extract response and any tool results
            result = {
                "query": query,
                "response": response.text,
                "tool_calls": []
            }
            
            # Check if the model made any function calls
            if hasattr(response, '_result') and response._result.candidates:
                candidate = response._result.candidates[0]
                if hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call'):
                            # Log the function call
                            func_call = part.function_call
                            result["tool_calls"].append({
                                "function": func_call.name,
                                "args": dict(func_call.args) if func_call.args else {}
                            })
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            return {
                "query": query,
                "error": str(e),
                "response": "I encountered an error while analyzing your request. Please check the logs for details."
            }
    
    def get_similar_queries(self, query: str) -> List[Dict[str, Any]]:
        """Get similar successful queries from cache."""
        return cache_manager.get_similar_patterns(query)
    
    def reset_session(self):
        """Reset the conversation session."""
        self._initialize_chat()
        logger.info("Session reset")

def create_manufacturing_analyst(use_minimal_context: bool = False) -> ManufacturingAnalystAgent:
    """Factory function to create a Manufacturing Analyst Agent.
    
    Args:
        use_minimal_context: Use minimal context for testing
        
    Returns:
        Configured ManufacturingAnalystAgent instance
    """
    return ManufacturingAnalystAgent(use_minimal_context=use_minimal_context)