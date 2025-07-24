#!/usr/bin/env python3
"""Quick test to compare guided vs unguided discovery."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from adk_agents.tests.validation.run_guided_discovery import run_comparison

if __name__ == "__main__":
    asyncio.run(run_comparison())