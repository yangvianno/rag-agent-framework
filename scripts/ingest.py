# scripts/ingest.py - acts as dispatcher, handling routing and database population

import os
import click
import uuid
from pathlib import Path
# -- Add project root to path to allow submodule imports --
import sys
project_root = Path(__file__).resolve().parent[1]
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'vendor'))

from src.rag_agent_framework.utils.db_connections      import DatabaseConnections
from src.rag_agent_framework.ingestion.document_parser import parse_document
from src.rag_agent_framework.ingestion.cad_parser      import parse_step_file
from src.rag_agent_framework.rag.text_splitter         import split_documents
from src.rag_agent_framework.core.config               import config
from langchain_community.embeddings                    import OllamaEmbeddings
from langchain.schema                                  import Document
from qdrant_client.http                                import models

# -- Constants -- from config.yaml
QDRANT_COLLECTION_NAME = config.vector_db.default_collection_name
EMBEDDING_MODEL        = "nomic-embed-text:latest"
MARKDOWN_EXTENSIONS    = ['.pdf', '.docx', '.md', '.html', '.pptx', '.txt']
CAD_EXTENSIONS         = ['.step', 'iges']

def get_embedder():
    return OllamaEmbeddings(model=EMBEDDING_MODEL)

def process_and_store(file_path: str, db_manager: DatabaseConnections, embeddings):
    """Processes a single file, stores its content in Qdrant, and its metadata in Neo4j"""
    try:
        qdrant_client = db_manager.get_qdrant_client()
        neo4j_driver  = db_manager.get_neo4j_driver()
        file_ext      = Path(file_path).suffic.lower()
        filename      = os.path.basename(file_path)

        # -- Dispatcher Logic --
        # 1. Hanfle CAD files
        if file_ext in CAD_EXTENSIONS:
            cad_data = parse_step_file(file_path)
            with neo4j_driver.session() as session:
                for part in cad_data['parts']:
                    session.run("""
                        MERGE (p:Part {part_id: $part_id})
                        SET p.volume = $volume, p.source_file = $filename""",
                        part_id = part["part_id"],
                        volume  = part["volume"],
                        filename= filename
                    )
                    print(f"✔️  Created Part node in Neo4j for: {part['part_id']}")

                    # Store a text summary for the part in Qdrant
                    qdrant_client.add(
                        collection_name = QDRANT_COLLECTION_NAME,
                        document        = [part['properties_text']],
                        ids             = [str(uuid.uuid4())],
                        metadatas       = [{"source": filename, "part_id": part['part_id'], "type": "cad_summary"}]
                    )
                    print(f"✔️  Stored vector summary in Qdrant for: {part['part_id']}")

        # 2. Handle Text-based Documents
        elif file_ext in MARKDOWN_EXTENSIONS:
            content      = parse_document(file_path)
            # Wraps raw text in a LangChain Document to use the text_splitter.py
            temp_doc     = [Document(page_content=content, metadata={"source": filename})]  
            chunked_docs = split_documents(
                temp_doc,
                chunk_size    = config.retriever.chunk_size,
                chunk_overlap = config.retriever.chunk_overlap
            )
            chunk_texts  = [doc.page_content for doc in chunked_docs]

            # Creates a single Document node in the graph
            document_id = str(uuid.uuid4())
            with neo4j_driver.session() as session:
                session.run("""
                    MERGE (d:Document {source_path: $source_path})
                    SET d.document_id = $document_id, d.filename = $filename""",
                    source_path = file_path,
                    document_id = document_id,
                    filename    = filename
                )
            print(f"✔️  Created Document node in Neo4j for: {filename}")

            # Embed all chunks and store them in Qdrant
            qdrant_client.add(
                collection_name = QDRANT_COLLECTION_NAME,
                documents       = chunk_texts,
                ids             = [str(uuid.uuid4()) for _ in chunk_texts],
                metadatas       = [{"source": filename, "document_id": document_id, "type": "text_chunk"} for _ in chunk_texts]
            )
            print(f"️✔️  Stored {len(chunk_texts)} text chunks in Qdrant for: {filename}")
        
        else:
            print(f"⚠️ Unsupported file type: {filename}. Skipping.")
            return
    
    except Exception as e:
        print(f"❌ Failed to process {file_path}. Error: {e}")

@click.command()
@click.option('--path', default='./data', help='Path to the directory or a single file to ingest')
def ingest(path):
    """Ingest documents from a specified path into the hybrid knowledge base, populating both the Qdrant vector store and the Neo4j graph database"""
    db_manager = DatabaseConnections

            





import os
import argparse
from pathlib import Path
# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

import qdrant_client
from qdrant_client.http import models
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
            vectors_config = models.VectorParams(
                size    = vector_size,
                distance= models.Distance.COSINE,
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
    client         = qdrant_client.QdrantClient(url = qdrant_url)
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