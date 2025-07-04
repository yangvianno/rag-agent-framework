# scripts/query.py

import os
import sys
import argparse
from pathlib import Path

# This block ensures the 'src' dir is on the Python path
project_root = Path(__file__).resolve().parents[1]
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
load_dotenv()
# Import the LCEL chain function
from rag_agent_framework.rag.rag_chain import get_rag_chain

# A command-line interface to query the RAG chain.
def main():
    parser = argparse.ArgumentParser(description="Query your RAG chain from the command line")
    parser.add_argument("query", type=str, help="The question you want to ask.")
    parser.add_argument("-c", "--collection", default="my_rag_collection", help="The Qdrant collection to query.")
    args = parser.parse_args()

    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url: raise RuntimeError("QDRANT_URL not set. Please check your .env file.")

    # 1. Build the RAG chain
    print("Building RAG chain...")
    chain = get_rag_chain(args.collection, qdrant_url)

    # 2. Invoke the chain with the query
    print(f"Querying collection '{args.collection}'...")
    print("-" * 30)
    # The new LCEL chain expects a simple string input, not a dictionary
    result = chain.invoke(args.query)

    # 3. Print the result
    print("--- RAG Answer ---")
    print(result)
    print("-" * 30)

if __name__ == "__main__":
    main()
