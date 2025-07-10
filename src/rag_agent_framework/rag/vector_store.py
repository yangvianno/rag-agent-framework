# src/rag_agent_framework/rag/vector_store.py -- Chef (construction crew is init_collection.py). Its job is to connect to the kitchen that is already built. It puts your PDF information (ingredients) onto the shelves and pulls them out later to answer questions. It doesn't have the power to destroy the shelves.
import os
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_community.embeddings.ollama import OllamaEmbeddings
from rag_agent_framework.core.config import LLM_CFG, OPENAI_API_KEY, OLLAMA_URL

"""
	1. We instantiate a QdrantClient once, then wrap it in LangChain’s QdrantVectorStore class for easy document add/query.
    2. We pull in the Qdrant URL from the provided argument.
    3. We create an embeddings object (OpenAI or Ollama) based on LLM_CFG and available environment variables.	
"""

def get_vector_store(collection_name: str, url: str) -> QdrantVectorStore:
    if not url: raise ValueError("Qdrant URL must be provided.")
    
    # 1. Initialize embedding function based on config
    if LLM_CFG["default"] == "openai":
        embeddings = OpenAIEmbeddings(
            model = LLM_CFG["openai"]["embedding_model"],
            openai_api_key = OPENAI_API_KEY
        )
        
    else:
        embeddings = OllamaEmbeddings(
            model = LLM_CFG["ollama"]["embedding_model"],
            base_url = OLLAMA_URL
        )

    # 2. Initialize Qdrant client
    client = QdrantClient(url = url)

    # 3. Returns a LangChain vectore store wrapper around an existing Qdrant collection
    return QdrantVectorStore(
        client = client,
        collection_name = collection_name,
        embedding = embeddings,
    )

