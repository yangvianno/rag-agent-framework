# scripts/run_crew.py -- Crew Runner Script -- main entry point for interacting with agentic system

import os
import sys
import argparse
from pathlib import Path

# --- Path fix: Ensures the 'src' directory is on the Python path ---
project_root = Path(__file__).resolve().parents[1]
src_path = project_root / "src"     # Doesnt mean creating new empty "/src" but merely creates a complete separate Path object in memory then tells system "I intend to work with.."
if not src_path.exists():               # When specifically points to the /src in the sys.path but if not exists then raiseError
    raise FileNotFoundError(f"'src' folder not found at {src_path}")
if str(src_path) not in sys.path:       # if /src exists but not found? Added to the sys.path
    sys.path.insert(0, str(src_path))
# --- End Path fix ---

from dotenv import load_dotenv
load_dotenv()
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