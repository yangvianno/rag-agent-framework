# src/rag_agent_framework/api/server.py -- The main FastAPI server, adapting the logic from chat.py

import io
import os
from crewai                                 import Crew
from fastapi                                import FastAPI, HTTPException, Body, UploadFile, File, Form
from pydantic                               import BaseModel, Field
from typing                                 import Optional
from fastapi.concurrency                    import run_in_threadpool # For running sync code in async endpoints
from langchain_core.messages                import HumanMessage
from langchain_openai                       import ChatOpenAI
from langchain_community.chat_models.ollama import ChatOllama

from rag_agent_framework.agents.crew import agent_crew
from rag_agent_framework.rag.memory  import MemoryStore, get_summarizer
from rag_agent_framework.core.config import AGENT_CFG, QDRANT_URL, LLM_CFG, OLLAMA_URL, OPENAI_API_KEY

# Initialize FastAPI app
app = FastAPI(
    title = "RAG Agent Framework API",
    description = "An API for interacting with a RAG-powered agentic crew",
    version = "1.0.0"
)

# --- Pydantic Models for API I/O --- Defines the expected structure of incoming/outgoing JSON payloads for /chat
class ChatRequest(BaseModel):
    question: str
    user_id: Optional[str] = Field(
        default_factory = lambda: AGENT_CFG.get("default_user_id", "user123"),
        description = "Unique identifier for the user"
    )

class ChatResponse(BaseModel):   
    answer: str
    user_id: str
    memory_summary: Optional[str] = None

# --- API Endpoints ---
@app.get("/", summary = "Root endpoint to check API status")
def read_root():
    """/ -> Root: A simple endpoint to confirm the API is running"""
    return {"status": "ok", "message": "Welcome to the RAG Agent Framework API!"}

@app.post("/chat", response_model=ChatResponse, summary="Handle a chat interaction")
async def chat_with_agent(request: ChatRequest = Body(...)):
    """
        /chat -> Main chat endpoint
        1. MemoryStore initialized for specific user_id (+ get_memories)
        2. inputs{} combines user question and memory_context into dict passed to the agent crew
        3. agent_crew.kickoff(inputs) inside run_in_threadpool since it's synchronous
        4. get_summarizer(user's question + agent's response) in threadpool -> MemoryStore
    """
    
    print(f"Received chat request for user '{request.user_id}' with question: '{request.question}'")
    try:
        # 1. Initialize memory store for the user
        memory_store = MemoryStore(user_id=request.user_id)

        # 2. Retrieve relevant memories
        print(f"Retrieving memories for query: {request.question}")
        relevant_memories   = memory_store.get_memories(query = request.question)
        memory_context      = "\n".join([mem.page_content for mem in relevant_memories])
        print(f"Retrieved context: {memory_context}")

        # 3. Prepare inputs for the crew, including the memory context
        inputs = {
            "topic": request.question,
            "context": memory_context if memory_context else "No relevant past conversations found"
        }

        # 4. Kick off the crew's task
        print("Kicking off the agent crew in a background thread...")
        result = await run_in_threadpool(agent_crew.kickoff, inputs=inputs)
        # result = agent_crew.kickoff(inputs=inputs)      # Gives that memory + question to a group of agents (the “crew”) to figure out the answer.
        print(f"Crew finished with result: {result}")

        # 5. Summarize the interaction for long-term memory
        summarizer_chain          = get_summarizer()
        conversation_to_summarize = f"User Question: {request.question}\nAgent Answer: {result}"
        llm_response              = await run_in_threadpool(summarizer_chain.invoke, {"text": conversation_to_summarize})
        summary                   = llm_response.content

        # 6. Add the new summary to the memory store
        memory_store.add_memory(summary)

        return ChatResponse(
            answer         = str(result),
            user_id        = request.user_id,
            memory_summary = summary
        )

    except Exception as e:
        # Logs the error on the server terminal/logs
        print(f"An unexpected error occurred: {e}")
        print(f"Error details: {repr(e)}")
        
        # Sends the user a friendly, generic message
        raise HTTPException(
            status_code = 500,
            detail      = "An error occurred while processing your request with the agent crew. Please check the server logs for details."
        )
    
@app.post("/upload", summary = "Upload a document to the knowledge base")
async def upload_document(
    collection_name: str = Form("my_rag_collection"), 
    file: UploadFile     = File(...)
):
    """
        /upload -> Upload documents to KB
        1. Reads the uploaded docs to io.BytesIO -> temp_file
        2. Initializes MemoryStore for given collection_name (not tied to general) <- temp_file
        Uploads a document to the specified Qdrant collection. This is used to populate the knowledge base for the document_researcher agent.
    """
    print(f"Received file '{file.filename}' for collection '{collection_name}'")
    try:
        # Read the file content into an in-memory object
        file_content    = await file.read()
        temp_file       = io.BytesIO(file_content)
        temp_file.name  = file.filename

        # We initialize it with a collection_name instead of a user_id to target the general knowledge base.
        doc_store = MemoryStore(collection_name=collection_name, url=QDRANT_URL)
        
        # Add the document to the vector store
        await run_in_threadpool(doc_store.add_document, temp_file)
        
        print(f"Successfully processed and stored '{file.filename}'")
        return {"message": f"Successfully uploaded {file.filename} to collection '{collection_name}'."}

    except Exception as e:
        print(f"Error during file upload: {e}")
        print(f"Error details: {repr(e)}")
        raise HTTPException(
            status_code = 500,
            detail      = f"An error occurred during file upload: {str(e)}"
        )
    

@app.get("/health", summary = "Health check endpoint")
def health_check():
    """/health -> Confirm the API is running and healthy"""
    return {"status": "healthy"}