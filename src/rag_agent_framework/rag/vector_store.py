# src/rag_agent_framework/rag/vector_store.py

from qdrant_client import QdrantClient, models
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_community.embeddings.ollama import OllamaEmbeddings
from rag_agent_framework.core.config import LLM_CFG, OPENAI_API_KEY, OLLAMA_URL

"""
	1. We instantiate a QdrantClient once, then wrap it in LangChain’s Qdrant class for easy document add/query.	
    2. We pull in your Qdrant URL and gRPC preference.
	3. We create an OpenAIEmbeddings object using your OPENAI_API_KEY.	
"""

def get_vector_store(collection_name: str, url: str) -> QdrantVectorStore:
    if not url: raise ValueError("Qdrant URL must be provided.")
    
    # 1. Initialize embedding function based on config
    if LLM_CFG["default"] == "openai":
        embeddings = OpenAIEmbeddings(model = LLM_CFG["openai"]["embedding_model"],
                                      openai_api_key = OPENAI_API_KEY)
        
    else:
        embeddings = OllamaEmbeddings(model = LLM_CFG["ollama"]["embedding_model"],
                                      url = OLLAMA_URL)

    # 2. Initialize Qdrant client
    client = QdrantClient(url = url)

    # 3. Get the vector size from the embedding model -- Prepares Qdrant database before adding any documents
    vector_size = len(embeddings.embed_query("test"))                       # Detects size of chosen AI model creates
    client.recreate_collection(collection_name = collection_name,           # Create empty collection, ready for my data
                               vectors_config = models.VectorParams(size = vector_size,                     # Configures the collection to accept vectors of the exact size we just detected.
                                                                    distance = models.Distance.COSINE))     # Tells the database to use "Cosine Similarity" to measure how alike your text chunks are. This is a very effective standard for text embeddings.
    print(f"Collection '{collection_name}' created or recreated successfully.")

    # Returns a LangChain wrapper around a Qdrant collection
    return QdrantVectorStore(client = client,
                  collection_name = collection_name,
                  embedding = embeddings,)

