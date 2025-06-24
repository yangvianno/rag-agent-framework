# scripts/ingest.py - a standalone CLI to ingest a PDF/URL into Qdrant

import argparse
from rag_agent_framework.rag.data_loader import load_documents
from rag_agent_framework.rag.text_splitter import split_documents
from rag_agent_framework.rag.vector_store import get_vector_store

"""

"""

def main():
    parser = argparse.ArgumentParser(description = "Ingest a local PDF or a remote URL into your Qdrant vector store.")
    parser.add_argument("-s", "--source", required = True,
                        help = "Path to a PDF on disk or a URL to ingest")
    parser.add_argument("-c", "--collection", default = "my_rag_collection",
                        help = "Name of the Qdrant collection (default to 'my_rag_collection')")
    args = parser.parse_args()

    print(f"Ingest from {args.source} into collection '{args.collection}'...")

    docs = load_documents(args.source)                          # 1. Load
    chunks = split_documents(docs)                              # 2. Chunk
    db = get_vector_store(collection_name = args.collection)    # 3. Upsert into Qdrant
    db.add_document(chunks)
    print(f"✅ Ingested {len(chunks)} chunks into '{args.collection}'.")

if __name__ == "__main__":
    main()