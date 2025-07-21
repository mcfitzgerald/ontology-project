#!/usr/bin/env python3
"""
Simple script to run ADK evaluations programmatically
"""
import asyncio
import sys
from pathlib import Path
from google.adk.evaluation.agent_evaluator import AgentEvaluator

async def run_evaluation():
    """Run the evaluation for the manufacturing agent"""
    
    # Run discovery-first evaluation
    print("Running discovery-first evaluation...")
    try:
        await AgentEvaluator.evaluate(
            agent_module="manufacturing_agent",
            eval_dataset_file_path_or_dir="evaluation/evalsets/discovery_first.evalset.json",
        )
        print("✅ Discovery-first evaluation completed")
    except Exception as e:
        print(f"❌ Discovery-first evaluation failed: {e}")
        
    # Run hidden capacity evaluation
    print("\nRunning hidden capacity evaluation...")
    try:
        await AgentEvaluator.evaluate(
            agent_module="manufacturing_agent",
            eval_dataset_file_path_or_dir="evaluation/evalsets/hidden_capacity.evalset.json",
        )
        print("✅ Hidden capacity evaluation completed")
    except Exception as e:
        print(f"❌ Hidden capacity evaluation failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_evaluation())