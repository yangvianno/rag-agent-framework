# scripts/run_crew.py -- Crew Runner Script -- main entry point for interacting with agentic system

import os
import sys
import argparse
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()
from rag_agent_framework.utils import path_fix # noqa: F401
from rag_agent_framework.agents.crew import agent_crew      # instead of get_crew for more flexible, recreate the crew dynamically, change its config, etc.

def main():
    """A command-line interface to run the agentic crew"""
    parser = argparse.ArgumentParser(description="Run the agentic crew with a specific tasks")
    parser.add_argument("topic", type=str, help="The topic of the question for the crew to research")
    args = parser.parse_args()

    # Prepare the inputs for the crew's kickoff
    inputs = {
        "topic": args.topic,
        "context": "No conversational context provided for this run"
    }

    print(f"🚀 Kicking off the crew for topic: {args.topic}")
    print("-" * 100)

    # Run the crew
    result = agent_crew.kickoff(inputs = inputs)

    print("\n\n--- Crew Run Complete ---")
    print("Final Result:")
    print(result)
    print("-" * 100)

if __name__ == "__main__":
    main()