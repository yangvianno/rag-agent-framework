# scripts/ingest.py - a standalone CLI to ingest a PDF/URL into Qdrant

import os
import argparse
from pathlib import Path
# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

import qdrant_client
from qdrant_client.http import models as rest
from rag_agent_framework.rag.data_loader import load_documents
from rag_agent_framework.rag.text_splitter import split_documents
from rag_agent_framework.rag.vector_store import get_vector_store
from rag_agent_framework.core.config import config

"""
	1.	Load your PDF or fetch & parse the URL
	2.	Split it into chunks
	3.	Upsert those chunks into your Qdrant collection
"""

# --- Helper Function ---
def create_collection_if_not_exists(client: qdrant_client.QdrantClient, collection_name: str, vector_size: int):
    """Creates a Qdrant collection if it doesn't already exist."""
    try:
        client.get_collection(collection_name = collection_name)
        print(f"Collection '{collection_name}' already exists.")
    except Exception:
        print(f"Collection '{collection_name}' not found. Creating new collection...")
        client.recreate_collection(
            collection_name = collection_name,
            vectors_config = rest.VectorParams(
                size    = vector_size,
                distance= rest.Distance.COSINE,
            ),
        )
        print(f"Collection '{collection_name}' created successfully.")

def main():
    parser = argparse.ArgumentParser(description = "Ingest a local PDF or a remote URL into your Qdrant vector store.")
    parser.add_argument("-s", "--source", required = True,
                        help = "Path to a PDF on disk or a URL to ingest")
    parser.add_argument("-c", "--collection", default = config.vector_db.default_collection_name,
                        help = "Name of the Qdrant collection (default to 'my_rag_collection')")
    args = parser.parse_args()

    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        raise ValueError("QDRANT_URL environment variable not set.")

    print(f"Ingest from {args.source} into collection '{args.collection}'...")
    
    # Ensure the collection exists
    client = qdrant_client.QdrantClient(url = qdrant_url)
    embedding_dims = config.llm.openai.embedding_dims
    create_collection_if_not_exists(client, args.collection, embedding_dims)

    docs = load_documents(Path(args.source))    # 1. Load

    print(f"Splitting documents with chunk_size={config.retriever.chunk_size} and chunk_overlap={config.retriever.chunk_overlap}")   # 2. Chunk
    nodes = split_documents(docs, chunk_size=config.retriever.chunk_size, chunk_overlap=config.retriever.chunk_overlap)                

    db = get_vector_store(collection_name = args.collection, url = qdrant_url)     # 3. Upsert into Qdrant
    db.add_documents(nodes)

    print(f"✅ Ingested {len(nodes)} chunks into '{args.collection}'.")

if __name__ == "__main__":
    main() 