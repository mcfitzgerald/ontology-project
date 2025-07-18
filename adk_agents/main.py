#!/usr/bin/env python3
"""Main runner for ADK Manufacturing Analytics Agent."""
import sys
import logging
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adk_agents.agents.manufacturing_analyst import create_manufacturing_analyst
from adk_agents.config.settings import LOG_LEVEL, LOG_FORMAT

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('adk_agents.log')
    ]
)

logger = logging.getLogger(__name__)

def print_welcome():
    """Print welcome message."""
    print("\n" + "="*60)
    print("ADK Manufacturing Analytics Agent")
    print("="*60)
    print("\nAsk questions about your manufacturing data:")
    print("- 'What's the OEE performance across our production lines?'")
    print("- 'Show me quality trends for the last 30 days'")
    print("- 'Calculate ROI if we improve Line A to 85% OEE'")
    print("- 'Find equipment with performance below 70%'")
    print("\nCommands:")
    print("- 'help' - Show this message")
    print("- 'cache' - Show cache statistics")
    print("- 'reset' - Reset conversation session")
    print("- 'quit' or 'exit' - Exit the program")
    print("="*60 + "\n")

def format_response(result: dict) -> str:
    """Format agent response for display."""
    output = []
    
    # Main response
    if "response" in result:
        output.append(f"\n{result['response']}")
    
    # Tool call results (if verbose)
    if "tool_calls" in result and result["tool_calls"]:
        output.append("\n--- Tool Calls ---")
        for call in result["tool_calls"]:
            output.append(f"\nFunction: {call['function']}")
            if isinstance(call['result'], dict):
                if "error" in call['result']:
                    output.append(f"Error: {call['result']['error']}")
                else:
                    # Pretty print JSON results
                    output.append(json.dumps(call['result'], indent=2)[:500] + "...")
    
    # Error handling
    if "error" in result:
        output.append(f"\nError: {result['error']}")
    
    return "\n".join(output)

def main():
    """Main conversation loop."""
    print_welcome()
    
    # Create agent
    try:
        logger.info("Initializing Manufacturing Analyst Agent...")
        agent = create_manufacturing_analyst(use_minimal_context=False)
        logger.info("Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        print(f"Error: Failed to initialize agent - {e}")
        print("Please check your configuration and try again.")
        return
    
    # Conversation loop
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit']:
                print("\nGoodbye!")
                break
            
            elif user_input.lower() == 'help':
                print_welcome()
                continue
            
            elif user_input.lower() == 'cache':
                from adk_agents.tools.cache_manager import cache_manager
                summary = cache_manager.get_cache_summary()
                print("\n--- Cache Statistics ---")
                print(json.dumps(summary, indent=2))
                continue
            
            elif user_input.lower() == 'reset':
                agent.reset_session()
                print("\nSession reset. Starting fresh conversation.")
                continue
            
            elif not user_input:
                continue
            
            # Process query
            print("\nAnalyzing...")
            
            # Log the query
            logger.info(f"User query: {user_input}")
            
            # Get response
            result = agent.analyze(user_input)
            
            # Log the response
            logger.info(f"Agent response: {result.get('response', 'No response')[:200]}...")
            
            # Display response
            print(format_response(result))
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'quit' to exit.")
            continue
        
        except Exception as e:
            logger.error(f"Error in conversation loop: {e}", exc_info=True)
            print(f"\nError: {e}")
            print("Type 'help' for assistance or 'quit' to exit.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nFatal error: {e}")
        sys.exit(1)