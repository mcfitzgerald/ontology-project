#!/usr/bin/env python3
"""Unified CLI interface using the same ADK agent as the web interface."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from adk_agents.manufacturing_agent.agent import root_agent

async def run_cli():
    """Run the manufacturing analyst in CLI mode using ADK Runner."""
    # Use the SAME agent as the web interface
    runner = InMemoryRunner(agent=root_agent, app_name="manufacturing_cli")
    
    # Create a session
    session = await runner.session_service.create_session(
        app_name="manufacturing_cli",
        user_id="cli_user",
        session_id="cli_session"
    )
    
    print("=" * 60)
    print("Manufacturing Analyst CLI")
    print("Using Google Agent Development Kit")
    print("=" * 60)
    print("\nI'm your Manufacturing Analyst, ready to help you discover optimization")
    print("opportunities in your manufacturing data using SPARQL queries and analysis.")
    print("\nCommands:")
    print("  - Type your questions or analysis requests")
    print("  - 'help' - Show available commands")
    print("  - 'reset' - Start a new conversation")
    print("  - 'exit' or 'quit' - Exit the CLI")
    print("\n" + "=" * 60)
    
    session_id = "cli_session"
    session_counter = 1
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit']:
                print("\nGoodbye!")
                break
                
            if user_input.lower() == 'help':
                print("\nAvailable commands:")
                print("  - Ask questions about your manufacturing data")
                print("  - Request analysis of equipment performance, OEE, downtime, etc.")
                print("  - 'reset' - Start a new conversation session")
                print("  - 'exit' or 'quit' - Exit the CLI")
                continue
                
            if user_input.lower() == 'reset':
                # Create a new session
                session_counter += 1
                session_id = f"cli_session_{session_counter}"
                session = await runner.session_service.create_session(
                    app_name="manufacturing_cli",
                    user_id="cli_user",
                    session_id=session_id
                )
                print("\nConversation reset. Starting fresh!")
                continue
            
            # Create message
            message = Content(parts=[Part(text=user_input)])
            
            # Run agent and print response
            print("\nAnalyst: ", end="", flush=True)
            response_parts = []
            
            async for event in runner.run_async(
                user_id="cli_user",
                session_id=session_id, 
                new_message=message
            ):
                if event.is_final_response() and event.content:
                    for part in event.content.parts:
                        if part.text:
                            response_parts.append(part.text)
                            print(part.text, end="", flush=True)
                        # Handle other part types if needed (images, etc.)
            
            print()  # New line after response
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'exit' to quit or continue with your questions.")
            continue
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again or type 'exit' to quit.")

if __name__ == "__main__":
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)