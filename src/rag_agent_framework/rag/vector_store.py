# src/rag_agent_framework/rag/vector_store.py

from qdrant_client import QdrantClient
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Qdrant
from rag_agent_framework.core.config import VECTOR_DB_CFG, OPENAI_API_KEY

"""
	1.	We pull in your Qdrant URL and gRPC preference from VECTOR_DB_CFG.
	2.	We create an OpenAIEmbeddings object using your OPENAI_API_KEY.
	3.	We instantiate a QdrantClient once, then wrap it in LangChain’s Qdrant class for easy document add/query.
"""


# 1. Embedding function using your OpenAI key
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# 2. Qdrant client (will auto-create collections as needed)
client = QdrantClient(url=VECTOR_DB_CFG["url"],
                      prefer_grpc=VECTOR_DB_CFG.get("prefer_grpc", False))  # Prefer gRPC / HTTP to communicate with the Qdrant server

# Returns a LangChain wrapper around a Qdrant collection
def get_vector_store(collection_name: str = "my_rag_collection") -> Qdrant:
    return Qdrant(client = client,
                  collection_name = collection_name,
                  embeddings = embeddings,
                  prefer_grpc = VECTOR_DB_CFG.get("prefer_grpc", False))

