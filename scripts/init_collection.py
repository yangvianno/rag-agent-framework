# scripts/init_collection.py -- Construction Crew. Its only job is to build and set up your empty database (the kitchen shelves). It has the power to destroy everything and start fresh (recreate_collection)

import os
from dotenv import load_dotenv
load_dotenv()
from qdrant_client import QdrantClient, models
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings.ollama import OllamaEmbeddings
from rag_agent_framework.core.config import LLM_CFG, VECTOR_DB_CFG, OPENAI_API_KEY, OLLAMA_URL, QDRANT_URL

if not QDRANT_URL: raise RuntimeError("QDRANT_URL is not set in the environment.")

# 1. Pick the embedding backend
if LLM_CFG["default"] == "openai":
    embeddings = OpenAIEmbeddings(
        model = LLM_CFG["openai"]["embedding_model"],
        openai_api_key = OPENAI_API_KEY
    )
    print("⚙️  Using OpenAI embeddings.")
else:
    embeddings = OllamaEmbeddings(
        model = LLM_CFG["ollama"]["embedding_model"],
        base_url = OLLAMA_URL,
    )
    print("⚙️  Using Ollama embeddings.")

# 2. Stand up Qdrant client
client = QdrantClient(
    url = QDRANT_URL,
    prefer_grpc = VECTOR_DB_CFG.get("prefer_grpc", False)
)

# 3. Get the vector size from the embedding model -- Prepares Qdrant database before adding any documents
vector_size = len(embeddings.embed_query("test"))          # Detects size of chosen AI model creates

collections = ["my_rag_collection"]             # Add more collection names here if needed
for name in collections:
    client.recreate_collection(
        collection_name = name,          # Create empty collection, ready for my data
        vectors_config = models.VectorParams(
            size = vector_size,                     # Configures the collection to accept vectors of the exact size we just detected.
            distance = models.Distance.COSINE       # Tells the database to use "Cosine Similarity" to measure how alike the text chunks are. This is a very effective standard for text embeddings.
        )
    )     
    print(f"✅ Initialized collection: '{name}' (dimension: {vector_size})")