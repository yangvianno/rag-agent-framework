# scripts/ingest.py - a standalone CLI to ingest a PDF/URL into Qdrant

import sys
import os
import argparse
from pathlib import Path
# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

from rag_agent_framework.utils import path_fix # noqa: F401
from rag_agent_framework.rag.data_loader import load_documents
from rag_agent_framework.rag.text_splitter import split_documents
from rag_agent_framework.rag.vector_store import get_vector_store

"""
	1.	Load your PDF or fetch & parse the URL
	2.	Split it into chunks
	3.	Upsert those chunks into your Qdrant collection
"""

def main():
    parser = argparse.ArgumentParser(description = "Ingest a local PDF or a remote URL into your Qdrant vector store.")
    parser.add_argument("-s", "--source", required = True,
                        help = "Path to a PDF on disk or a URL to ingest")
    parser.add_argument("-c", "--collection", default = "my_rag_collection",
                        help = "Name of the Qdrant collection (default to 'my_rag_collection')")
    args = parser.parse_args()

    # Get the URL from the environment here in the main script
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url: raise ValueError("QDRANT_URL environment variable not set or .env file not found.")

    print(f"Ingest from {args.source} into collection '{args.collection}'...")

    docs = load_documents(args.source)                                            # 1. Load
    chunks = split_documents(docs)                                                # 2. Chunk
    db = get_vector_store(collection_name = args.collection, url = qdrant_url)    # 3. Upsert into Qdrant
    db.add_documents(chunks)
    print(f"✅ Ingested {len(chunks)} chunks into '{args.collection}'.")

if __name__ == "__main__":
    main() 