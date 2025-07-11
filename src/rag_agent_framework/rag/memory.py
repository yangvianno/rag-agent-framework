# src/rag_agent_framework/rag/memory.py -- Manage per-user Qdrant memory collections and summarization

import os
from qdrant_client import QdrantClient, models
from qdrant_client.models import Filter, FieldCondition, MatchValue

from langchain_qdrant import QdrantVectorStore                      # Wraps Qdrant into a vectorStore interface that LangChain chains&retrievers can use, instead of calling QdrantClient directly
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from langchain_community.embeddings.ollama  import OllamaEmbeddings 
from langchain_community.chat_models.ollama import ChatOllama       # Chat-based LLM interface for Ollama models

from langchain_core.prompts         import ChatPromptTemplate       # Defines structured prompt templates to chat models
from langchain_core.output_parsers  import StrOutputParser
from langchain_core.runnables       import Runnable                 # Base clas for anything can be "run" in LangChain pipeline (models, chains, retrievers, etc.)

from langchain.schema import Document   # Used in RAG workflows to pass around the individual text chunks that also carry context about their origin.
from rag_agent_framework.core.config import LLM_CFG, OPENAI_API_KEY, OLLAMA_URL, QDRANT_URL
from rag_agent_framework.rag.vector_store import get_embedder
    
def _get_qdrant_client() -> QdrantClient:
    """Helper to get a Qdrant client instance"""
    return QdrantClient(url = QDRANT_URL)

# --- Memory Store Class ---
class MemoryStore:
    """Manages user-specific memories within a single, shared Qdrant collection."""
    
    _collection_name = "user_memory_store"      # The collection name is now a fixed, shared constant

    def __init__(self, user_id: str):
        """Initializes the memory store for a specific user."""
        self.user_id = user_id
        self.embedder = get_embedder()
        self.client = _get_qdrant_client()

        # This logic now ensures the SINGLE shared collection exists. It will only create the collection on the very first run for any user.
        try:
            self.client.get_collection(collection_name = self._collection_name)
        except Exception:
            # If it doesn't exist, create it.
            vector_size = len(self.embedder.embed_query("test"))
            # Create the collection because it does not exist
            self.client.create_collection(
                collection_name = self._collection_name,
                vectors_config = models.VectorParams(size = vector_size, distance = models.Distance.COSINE)
            )
            print(f"Created new shared memory collection: '{self._collection_name}'")

        # Initialize the store attribute
        self.store = QdrantVectorStore(
            client = self.client,
            collection_name = self._collection_name,
            embedding = self.embedder,
        )


    def add_memory(self, summary: str):
        """Adds a new memory summary with user_id in its metadata"""                                 
        # Create a Document with metadata before adding it
        memory_doc = Document(
            page_content = summary,
            metadata = {"user_id": self.user_id}
        )
        self.store.add_documents([memory_doc])
        print(f"Added new memory to collection '{self._collection_name}' for user '{self.user_id}'")

    def get_memories(self, query: str, k: int = 3) -> list[Document]:
        """Retrieves the most relevant memories for a given user using a metadata filter"""
        # A filter is added to the retriever to only search for this user's memories
        retriever = self.store.as_retriever(        # QdrantVectorStore
            search_kwargs = {
                "k": k,
                "filter": Filter(
                    must = [FieldCondition(key="user_id", match=MatchValue(value = self.user_id))]
                )
            }
        )
        print(f"Retrieving memories for user '{self.user_id}' relevant to: '{query}'")

        return retriever.invoke(query)
    
# --- Summarizer Chain ---
SUMMARIZER_PROMPT_TEMPLATE = """
Summarize the following conversation into a concise 2-3 sentence memory segment that captures the key information and user intent.

CONVERSATION:
{text}
"""

def get_summarizer() -> Runnable:
    """Builds and returns a modern summarizer chain using LCEL"""
    if LLM_CFG["default"] == "openai":
        llm = ChatOpenAI(
            model = LLM_CFG["openai"]["chat_model"],
            openai_api_key = OPENAI_API_KEY
        )
    else:
        llm = ChatOllama(
            model = LLM_CFG["ollama"]["chat_model"],
            base_url = OLLAMA_URL
        )
    
    prompt = ChatPromptTemplate.from_template(SUMMARIZER_PROMPT_TEMPLATE)

    # Use modern LCEL chain syntax
    summarizer_chain = prompt | llm | StrOutputParser()

    return summarizer_chain
