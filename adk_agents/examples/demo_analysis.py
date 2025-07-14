"""
Demo script showing how to use the ADK Manufacturing Analytics Agents.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from adk_agents.agents.orchestrator import create_orchestrator
from adk_agents.agents.explorer_agent import create_explorer_agent
from adk_agents.agents.query_agent import create_query_builder_agent
from adk_agents.agents.analyst_agent import create_analyst_agent
from adk_agents.config.settings import validate_config


class ManufacturingAnalyticsChat:
    """Main chat interface for manufacturing analytics."""
    
    def __init__(self):
        # Validate configuration
        validate_config()
        
        # Create agents
        self.explorer = create_explorer_agent()
        self.query_builder = create_query_builder_agent()
        self.analyst = create_analyst_agent()
        
        # Create orchestrator with sub-agents
        self.orchestrator = create_orchestrator([
            self.explorer,
            self.query_builder,
            self.analyst
        ])
        
        # Create runner
        self.runner = Runner(
            agent=self.orchestrator,
            app_name="manufacturing_analytics",
            session_service=InMemorySessionService()
        )
    
    async def analyze(self, user_question: str) -> str:
        """
        Process user question through agent pipeline.
        
        Args:
            user_question: Natural language question about manufacturing
        
        Returns:
            Analysis results with insights and recommendations
        """
        # Create user message
        user_content = types.Content(
            parts=[types.Part.from_text(user_question)]
        )
        
        # Run analysis
        session = await self.runner.session_service.create_session("demo_user")
        
        # Collect responses
        responses = []
        async for event in self.runner.run_async(
            user_id="demo_user",
            session_id=session.id,
            user_content=user_content
        ):
            if hasattr(event, 'content') and event.content:
                responses.append(event.content.parts[0].text)
        
        return "\n".join(responses)


# Example analyses matching the $2.5M opportunity
async def demo_hidden_capacity():
    """Demo: Find hidden capacity opportunities."""
    chat = ManufacturingAnalyticsChat()
    
    print("=== Hidden Capacity Analysis ===")
    response = await chat.analyze(
        "Which equipment has OEE below 85%? Calculate the financial impact "
        "of improving their performance to benchmark levels."
    )
    print(response)
    print()


async def demo_temporal_patterns():
    """Demo: Discover temporal patterns."""
    chat = ManufacturingAnalyticsChat()
    
    print("=== Temporal Pattern Discovery ===")
    response = await chat.analyze(
        "Are there patterns in when equipment failures or micro-stops occur? "
        "Focus on clustering and shift-based patterns. What's the financial impact?"
    )
    print(response)
    print()


async def demo_quality_analysis():
    """Demo: Quality-cost trade-off analysis."""
    chat = ManufacturingAnalyticsChat()
    
    print("=== Quality Impact Analysis ===")
    response = await chat.analyze(
        "Which products have the highest scrap rates? Calculate the financial "
        "impact of reducing scrap by 50% for high-margin products."
    )
    print(response)
    print()


async def demo_custom_question():
    """Demo: Answer custom question."""
    chat = ManufacturingAnalyticsChat()
    
    print("=== Custom Analysis ===")
    question = input("Enter your manufacturing question: ")
    response = await chat.analyze(question)
    print(response)
    print()


async def main():
    """Run demo analyses."""
    print("Manufacturing Analytics Agent Demo")
    print("==================================\n")
    
    while True:
        print("\nSelect analysis:")
        print("1. Hidden Capacity Analysis")
        print("2. Temporal Pattern Discovery")
        print("3. Quality Impact Analysis")
        print("4. Custom Question")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ")
        
        if choice == "1":
            await demo_hidden_capacity()
        elif choice == "2":
            await demo_temporal_patterns()
        elif choice == "3":
            await demo_quality_analysis()
        elif choice == "4":
            await demo_custom_question()
        elif choice == "5":
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())