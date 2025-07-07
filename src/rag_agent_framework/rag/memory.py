# src/rag_agent_framework/rag/memory.py -- Manage per-user Qdrant memory collections and summarization

import os
from qdrant_client import QdrantClient, models

from langchain_qdrant import QdrantVectorStore                      # Wraps Qdrant into a vectorStore interface that LangChain chains&retrievers can use, instead of calling QdrantClient directly
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from langchain_community.embeddings.ollama  import OllamaEmbeddings 
from langchain_community.chat_models.ollama import ChatOllama       # Chat-based LLM interface for Ollama models

from langchain_core.prompts         import ChatPromptTemplate       # Defines structured prompt templates to chat models
from langchain_core.output_parsers  import StrOutputParser
from langchain_core.runnables       import Runnable                 # Base clas for anything can be "run" in LangChain pipeline (models, chains, retrievers, etc.)

from langchain.schema import Document   # Used in RAG workflows to pass around the individual text chunks that also carry context about their origin.
from rag_agent_framework.core.config import LLM_CFG, VECTOR_DB_CFG

# --- Helper Functions ---
def get_embedder():
    if LLM_CFG["default"] == "openai":
        return OpenAIEmbeddings(openai_api_key = os.getenv("OPENAI_API_KEY"))
    else:
        return OllamaEmbeddings(
            model = LLM_CFG["ollama"]["embedding_model"],
            base_url = os.getenv("OLLAMA_URL")
        )
    
def _get_qdrant_client() -> QdrantClient:
    """Helper to get a Qdrant client instance"""
    return QdrantClient(url = os.getenv("QDRANT_URL"))

# --- Memory Store Class ---
class MemoryStore:
    """Manages a user-specific memory collection in Qdrant"""
    def __init__(self, user_id: str, base_collection: str = "user_memory"):
        self.collection_name = f"{base_collection}_{user_id}"
        self.embedder = get_embedder()
        self.client = _get_qdrant_client()

        # Ensure collection exists without wiping it
        try:
            self.client.get_collection(collection_name = self.collection_name)
            print(f"Memory collection '{self.collection_name}' already exists.")
        except Exception:
            # If it doesn't exist, create it.
            vector_size = len(self.embedder.embed_query("test"))
            self.client.creat_collection(
                collection_name = self.collection_name,
                vector_config = models.VectorParams(size = vector_size, distance = models.Distance.COSINE)
            )
            print(f"Created new memory collection: '{self.collection_name}' after ensuring no '{self.collection_name}' had been existed before.")

    def add_memory(self, summary: str):
        """Adds a new memory summary to the user's collection"""
        self.store.add_texts([summary])                                  # QdrantVectorStore

    def get_memories(self, query: str, k: int = 3) -> list[Document]:
        """Retrieves the most relevant memories for a given query"""
        retriever = self.store.as_retriever(search_kwargs = {"k": k})   # QdrantVectorStore

        return retriever.get_relevant_documents(query)
    
# --- Summarizer Chain ---
SUMMARIZER_PROMPT_TEMPLATE = """
Summarize the following coversation into a consise 2-3 sentences memory segment:
{text}
"""
def get_summarizer() -> Runnable:
    """Builds and returns a modern summarizer chain using LCEL"""
    if LLM_CFG["default"] == "openai":
        llm = ChatOpenAI(
            model = LLM_CFG["openai"]["chat_model"],
            openai_api_key = os.getenv("OPENAI_API_KEY")
        )
    else:
        llm = ChatOllama(
            model = LLM_CFG["ollama"]["model"],
            base_url = os.getenv("OLLAMA_URL")
        )
    
    prompt = ChatPromptTemplate.from_template(SUMMARIZER_PROMPT_TEMPLATE)

    # Use modern LCEL chain syntax
    summarizer_chain = prompt | llm | StrOutputParser()

    return summarizer_chain
