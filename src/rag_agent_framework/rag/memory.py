# src/rag_agent_framework/rag/memory.py -- Manage per-user Qdrant memory collections and summarization

import io       # Needed to handle files uploaded through the API as in-memory binary streams.
import os
import tempfile
# --- Qdrant and LangChain Imports ---
from langchain.schema                       import Document       # Used in RAG workflows to pass around the individual text chunks that also carry context about their origin.
from langchain_openai                       import ChatOpenAI
from langchain_community.chat_models.ollama import ChatOllama
from langchain.prompts                      import ChatPromptTemplate
from qdrant_client                          import QdrantClient, models
# --- Project-Specific Imports: The RAG Tools ---
from rag_agent_framework.rag.data_loader import load_documents
from rag_agent_framework.rag.text_splitter import split_documents
from rag_agent_framework.rag.vector_store import get_vector_store, get_embedder
from rag_agent_framework.core.config import *



# ==============================================================================
# 1. HELPER FUNCTION
# ==============================================================================
def _get_qdrant_client() -> QdrantClient:
    """Helper to get a Qdrant client instance"""
    return QdrantClient(url=QDRANT_URL)


# ==============================================================================
# 2. THE MemoryStore CLASS -- handle the two distinct memory types (Personal chat history for each user & A general knowledge library from uploaded documents)
# ==============================================================================

class MemoryStore:
    def __init__(self, user_id: str = None, collection_name: str = None, url: str = QDRANT_URL):
        if user_id: self.collection_name = f"user_{user_id}_memory"                     # For /chat endpoint for conversation history
        else:       self.collection_name = collection_name or "my_rag_collection"       # For /upload endpoint for the document knowledge base

        # Store the user_id if it exists, for tagging memories later
        self.user_id = user_id

        # Instantiate necessary clients and the vector store itself -- keeping the class self-contained
        self.client       = _get_qdrant_client()

# --- START: ADDED CODE to ensure user-specific collection exists ---
        try:
            self.client.get_collection(collection_name = self.collection_name)
            print(f"Collection '{self.collection_name}' already exists for user '{self.user_id or self.collection_name}'.")
        except Exception as e: # Catch any exception, specifically 'NotFoundError' from Qdrant
            print(f"Collection '{self.collection_name}' not found for user '{self.user_id or self.collection_name}'. Creating new collection.")
            
            # Determine vector size using the embedder
            embedder = get_embedder() 
            vector_size = len(embedder.embed_query("test query")) 
            
            # Create the new collection
            self.client.recreate_collection( # Using recreate_collection here for simplicity, create_collection is also an option if you don't want to inadvertently clear an existing one
                collection_name = self.collection_name,
                vectors_config  = models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
            )
            print(f"Successfully created collection '{self.collection_name}' for user '{self.user_id or self.collection_name}'.")
        # --- END: ADDED CODE ---

        self.vector_store = get_vector_store(
            collection_name = self.collection_name,
            url = url
        )

    # --- Methods for User Conversation Memory ---
    def get_memories(self, query: str, k: int = 5) -> list[Document]:
        """Retrieves the top 'k' most relevant chat summaries for a user by performing a vector similarity search"""
        print(f"🧠 Searching collection '{self.collection_name}' for memories relevant to: '{query}'")
        return self.vector_store.similarity_search(query, k=k)
    
    def add_memory(self, text: str):
        """Adds a new chat summary to the user's specific collection. This summary is wrapped in a Document object with user_id metadata"""
        doc = Document(page_content = text, metadata = {"user_id": self.user_id})
        self.vector_store.add_documents([doc])
        print(f"📝 Added memory to '{self.collection_name}' for user '{self.user_id}'")

    # --- Method for General Document Storage (The "Head Chef") --- 
    def add_document(self, file_obj: io.BytesIO):
        """Orchestrates the document processing pipeline by calling the specialized RAG tools in the correct order"""
        # 1. Temporarily save the uploaded file to 
        temp_file_path = f"./{file_obj.name}"
        with open(file_obj.name, "wb") as f: f.write(file_obj.getbuffer())


        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file_obj.name).suffix) as temp_file:
            temp_file.write(file_obj.getbuffer())
            temp_file_path = temp_file.name

        
        # 2. Call the Prep Station (data_loader.py)
        print(f"👨‍🍳 -> Calling data_loader to process file: {temp_file_path}")
        documents = load_documents(temp_file_path)
        
        os.remove(temp_file_path)

        if not documents:
            print(f"⚠️ Warning: Data loader could not extract content from {file_obj.name}.")
            return

        # 3. Call the Chopping Station (text_splitter.py).
        print(f"🔪 -> Calling text_splitter to chunk {len(documents)} document(s).")
        chunked_documents = split_documents(documents)
        
        # 4. Call the Line Cook (vector_store) to save the final product.
        print(f"✅ -> Storing {len(chunked_documents)} chunks in the vector store.")
        self.vector_store.add_documents(chunked_documents)
        print(f"Successfully added '{file_obj.name}' to the '{self.collection_name}' knowledge base.")

        
# ==============================================================================
# 3. SUMMARIZER HELPER FUNCTION
# ==============================================================================
SUMMARIZER_PROMPT_TEMPLATE = """
Summarize the following conversation into a concise 2-3 sentence memory segment that captures the key information and user intent.

CONVERSATION:
{text}
"""

def get_summarizer():
    """Builds and returns a simple and reusable LangChain (LCEL) chain that takes text and produces a summary"""
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
    prompt = ChatPromptTemplate.from_template(SUMMARIZER_PROMPT_TEMPLATE)       # Use modern LCEL chain syntax
    
    return prompt | llm
