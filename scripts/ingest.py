# scripts/ingest.py -- aparses, chunks, embeds, and stores (text and CAD files) into a hybrid knowledge base (Qdrant-vector search and Neo4j-graph based relationships)
# 1. Handles CLI input using click(--path option)
# 2. Initializes connections to Qdrant and Neo4j
# 3. Processes each file (dir or single file) using process_and_store()

import os
import click
import uuid
from pathlib import Path
# -- Add project root to path to allow submodule imports --
import sys
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'vendor/markitdown/packages/markitdown/src'))

from src.rag_agent_framework.utils.db_connections      import DatabaseConnections
from src.rag_agent_framework.ingestion.document_parser import parse_document
from src.rag_agent_framework.ingestion.cad_parser      import parse_step_file
from src.rag_agent_framework.rag.text_splitter         import split_documents
from src.rag_agent_framework.core.config               import config
from src.rag_agent_framework.rag.vector_store          import get_embedder
from langchain.schema                                  import Document
from qdrant_client.http                                import models

# -- Constants -- from config.yaml
QDRANT_COLLECTION_NAME = config.vector_db.default_collection_name
EMBEDDING_MODEL        = "nomic-embed-text:latest"
MARKDOWN_EXTENSIONS    = ['.pdf', '.docx', '.md', '.html', '.pptx', '.txt']
CAD_EXTENSIONS         = ['.step', 'iges']

def process_and_store(file_path: str, db_manager: DatabaseConnections, embeddings):
    """Processes a single file, stores its content in Qdrant, and its metadata in Neo4j"""
    try:
        qdrant_client = db_manager.get_qdrant_client()
        neo4j_driver  = db_manager.get_neo4j_driver()
        file_ext      = Path(file_path).suffix.lower()
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
                        documents       = [part['properties_text']],
                        embeddings      = [embeddings.embed_query(part['properties_text'])],
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
                embeddings      = embeddings.embed_documents(chunk_texts),
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
    # Collection setup for Qdrant (pre-processing step), Neo4j connection is not needed at this stage
    db_manager = DatabaseConnections()
    qdrant     = db_manager.get_qdrant_client()
    embeddings = get_embedder()

    # Ensure the Qdrant collection exists
    try:
        qdrant.get_collection(collection_name=QDRANT_COLLECTION_NAME)
        print(f"🗂️  Using existing Qdrant collection: '{QDRANT_COLLECTION_NAME}'")
    except Exception:
        print(f"✨ Creating new Qdrant collection: '{QDRANT_COLLECTION_NAME}'")
        # Dynamically get embedding size from the model
        vector_size = len(embeddings.embed_query("test"))
        qdrant.recreate_collection(
            collection_name = QDRANT_COLLECTION_NAME,
            vectors_config  = models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
        )

    # Process files
    if os.path.isdir(path):
        print(f"📂 Processing directory: {path}")
        for filename in os.listdir(path):
            if not filename.startswith('.'): # Skips hidden files
                file_path = os.path.join(path, filename)
                if os.path.isfile(file_path): process_and_store(file_path, db_manager, embeddings)
    
    elif os.path.isfile(path):
        print(f"📄 Processing single files: {path}")
        process_and_store(path, db_manager, embeddings)

    else:
        print(f"❌ Error: Provided path: '{path}' is not a valid file or directory.")
        return
    
    db_manager.close_connections()
    print(f"\n✅ Ingestion complete.")

if __name__ == '__main__':
    ingest()



