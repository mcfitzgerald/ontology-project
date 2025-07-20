"""Manufacturing Analyst Agent for MES data analysis."""
import logging
from typing import Dict, Any, List, Optional
import google.generativeai as genai

from ..context.context_loader import context_loader
from ..tools.sparql_tool import execute_sparql, get_successful_patterns
from ..tools.analysis_tools import analyze_patterns, calculate_roi, find_optimization_opportunities
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
            self.instruction = context_loader.get_minimal_context()
        else:
            self.instruction = context_loader.get_comprehensive_context()
        
        # Create the model
        self.model = self._create_model()
        
        # Initialize chat session
        self.chat = self.model.start_chat(history=[])
        
    def _create_model(self):
        """Create the LLM agent with tools."""
        # Define tools with proper signatures
        tools = [
            genai.types.Tool(
                function_declarations=[
                    genai.types.FunctionDeclaration(
                        name="execute_sparql",
                        description="Execute a SPARQL query against the MES ontology",
                        parameters={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The SPARQL query to execute"
                                }
                            },
                            "required": ["query"]
                        }
                    ),
                    genai.types.FunctionDeclaration(
                        name="analyze_patterns",
                        description="Analyze patterns in query results",
                        parameters={
                            "type": "object",
                            "properties": {
                                "data": {
                                    "type": "object",
                                    "description": "Query results to analyze"
                                },
                                "analysis_type": {
                                    "type": "string",
                                    "description": "Type of analysis: temporal, capacity, quality, or general",
                                    "enum": ["temporal", "capacity", "quality", "general"]
                                }
                            },
                            "required": ["data", "analysis_type"]
                        }
                    ),
                    genai.types.FunctionDeclaration(
                        name="calculate_roi",
                        description="Calculate ROI for performance improvements",
                        parameters={
                            "type": "object",
                            "properties": {
                                "current_performance": {
                                    "type": "number",
                                    "description": "Current performance percentage"
                                },
                                "target_performance": {
                                    "type": "number",
                                    "description": "Target performance percentage"
                                },
                                "annual_volume": {
                                    "type": "number",
                                    "description": "Annual production volume"
                                },
                                "unit_value": {
                                    "type": "number",
                                    "description": "Value per unit produced"
                                }
                            },
                            "required": ["current_performance", "target_performance", "annual_volume", "unit_value"]
                        }
                    ),
                    genai.types.FunctionDeclaration(
                        name="get_cache_summary",
                        description="Get summary of cached queries and patterns",
                        parameters={
                            "type": "object",
                            "properties": {}
                        }
                    )
                ]
            )
        ]
        
        # Create agent configuration
        agent_config = {
            "model": self.config.get("model", DEFAULT_MODEL),
            "instructions": self.instruction,
            "tools": tools
        }
        
        # Add API key if not using Vertex AI
        if "api_key" in self.config:
            agent_config["api_key"] = self.config["api_key"]
        
        return genai.types.Agent(**agent_config)
    
    def _handle_tool_call(self, tool_call: Dict[str, Any]) -> Any:
        """Handle tool function calls from the agent."""
        function_name = tool_call.get("name")
        args = tool_call.get("args", {})
        
        if function_name == "execute_sparql":
            return execute_sparql(args.get("query"))
        
        elif function_name == "analyze_patterns":
            return analyze_patterns(
                args.get("data"),
                args.get("analysis_type")
            )
        
        elif function_name == "calculate_roi":
            return calculate_roi(
                args.get("current_performance"),
                args.get("target_performance"),
                args.get("annual_volume"),
                args.get("unit_value")
            )
        
        elif function_name == "get_cache_summary":
            return cache_manager.get_cache_summary()
        
        else:
            return {"error": f"Unknown tool function: {function_name}"}
    
    def analyze(self, query: str) -> Dict[str, Any]:
        """Analyze a manufacturing query.
        
        Args:
            query: Business question or analysis request
            
        Returns:
            Analysis results with insights and recommendations
        """
        try:
            # Send query to agent
            response = self.session.send(
                message=query,
                agent=self.agent
            )
            
            # Process response
            result = {
                "query": query,
                "response": response.text if hasattr(response, 'text') else str(response),
                "tool_calls": []
            }
            
            # Handle any tool calls
            if hasattr(response, 'tool_calls'):
                for tool_call in response.tool_calls:
                    tool_result = self._handle_tool_call(tool_call)
                    result["tool_calls"].append({
                        "function": tool_call.get("name"),
                        "result": tool_result
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
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
        self.session = genai.live.LiveSession()
        logger.info("Session reset")

def create_manufacturing_analyst(use_minimal_context: bool = False) -> ManufacturingAnalystAgent:
    """Factory function to create a Manufacturing Analyst Agent.
    
    Args:
        use_minimal_context: Use minimal context for testing
        
    Returns:
        Configured ManufacturingAnalystAgent instance
    """
    return ManufacturingAnalystAgent(use_minimal_context=use_minimal_context)