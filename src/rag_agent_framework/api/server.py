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

# --- Pydantic Models for API I/O ---
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
    """A simple endpoint to confirm the API is running"""
    return {"status": "ok", "message": "Welcome to the RAG Agent Framework API!"}

@app.post("/chat", response_model=ChatResponse, summary="Handle a chat interaction")
async def chat_with_agent(request: ChatRequest = Body(...)):
    """
        Receives a user's question, orchestrate the agent crew to answer it,
        manages conversation memory, and returns the final answer
        This logic is adapted from scripts/chat.py
    """
    
    


    
    # --- START: TEMPORARY DEBUGGING CODE ---
    print("\n--- Starting direct LLM connection test (Temporary Debugging) ---")
    try:
        if LLM_CFG["default"] == "openai":
            llm_instance = ChatOpenAI(
                model=LLM_CFG["openai"]["chat_model"],
                openai_api_key=OPENAI_API_KEY,
                temperature=0,
                verbose=True
            )
            print(f"Initialized ChatOpenAI with model: {llm_instance.model}")

        elif LLM_CFG["default"] == "ollama": # Assuming LLM_CFG["default"] == "ollama"
            llm_instance = ChatOllama(
                model=LLM_CFG["ollama"]["chat_model"],
                base_url=OLLAMA_URL,
                temperature=0,
                verbose=True
            )
            print(f"Initialized ChatOllama with model: {llm_instance.model}, base_url: {llm_instance.base_url}")
        else:
            print("Error in test: Default LLM not configured or not supported in test script.")
            raise HTTPException(status_code=500, detail="LLM configuration for test is invalid.")

        print("Invoking LLM with a simple prompt in test...")
        # Use run_in_threadpool for the blocking LLM call within an async endpoint
        test_response = await run_in_threadpool(llm_instance.invoke, [HumanMessage(content="Hello, how are you?")])
        
        print("\n--- LLM Test Successful (Temporary Debugging) ---")
        print("Test response content:", test_response.content)
        
    except Exception as e:
        print("\n--- LLM Test FAILED (Temporary Debugging) ---")
        print(f"An error occurred during direct LLM test: {type(e).__name__}")
        print("Test Error details:", str(e))
        import traceback
        traceback.print_exc() # Print full traceback
        # Re-raise the exception or raise an HTTPException to indicate the test failed
        raise HTTPException(
            status_code=500,
            detail=f"LLM direct test failed: {type(e).__name__} - {str(e)}. Check server logs for full traceback."
        )
    print("\n--- Continuing with main chat logic ---")
    # --- END: TEMPORARY DEBUGGING CODE ---
    
    

    
    
    
    
    print(f"Received chat request for user '{request.user_id}' with question: '{request.question}'")
    try:
        # 1. Initialize memory store for the user
        memory_store = MemoryStore(user_id=request.user_id)

        # 2. Retrieve relevant memories
        print(f"Retrieving memories for query: {request.question}")
        relevant_memories = memory_store.get_memories(query=request.question)
        memory_context = "\n".join([mem.page_content for mem in relevant_memories])
        print(f"Retrieved context: {memory_context}")

        # 3. Prepare inputs for the crew, including the memory context
        inputs = {
            "topic": request.question,
            "context": memory_context if memory_context else "No reevant past conversations found"
        }

        # 4. Kick off the crew's task
        print("Kicking off the agent crew in a background thread...")
        result = await run_in_threadpool(agent_crew.kickoff, inputs=inputs)
        # result = agent_crew.kickoff(inputs=inputs)      # Gives that memory + question to a group of agents (the “crew”) to figure out the answer.
        print(f"Crew finished with result: {result}")

        # 5. Summarize the interaction for long-term memory
        summarizer_chain = get_summarizer()
        conversation_to_summarize = f"User Question: {request.question}\nAgent Answer: {result}"
        summary = await run_in_threadpool(summarizer_chain.invoke, {"text": conversation_to_summarize})
        # summary = summarizer_chain.invoke({"text": conversation_to_summarize})

        # 6. Add the new summary to the memory store
        memory_store.add_memory(summary)

        return ChatResponse(
            answer = str(result),
            user_id = request.user_id,
            memory_summary = summary
        )

    except Exception as e:
        # Logs the error on the server terminal/logs
        print(f"An unexpected error occurred: {e}")
        print(f"Error details: {repr(e)}")
        
        # Sends the user a friendly, generic message
        raise HTTPException(
            status_code = 500,
            detail = "An error occurred while processing your request with the agent crew. Please check the server logs for details."
        )
    
@app.post("/upload", summary="Upload a document to the knowledge base")
async def upload_document(
    collection_name: str = Form("my_rag_collection"), 
    file: UploadFile = File(...)
):
    """
    Uploads a document to the specified Qdrant collection. This is used 
    to populate the knowledge base for the document_researcher agent.
    """
    print(f"Received file '{file.filename}' for collection '{collection_name}'")
    try:
        # Read the file content into an in-memory object
        file_content = await file.read()
        temp_file = io.BytesIO(file_content)
        temp_file.name = file.filename

        # [Inference] This MemoryStore is used to access the vector DB.
        # We initialize it with a collection_name instead of a user_id
        # to target the general knowledge base.
        doc_store = MemoryStore(collection_name=collection_name, url=QDRANT_URL)
        
        # Add the document to the vector store
        await run_in_threadpool(doc_store.add_document, temp_file)
        
        print(f"Successfully processed and stored '{file.filename}'")
        return {"message": f"Successfully uploaded {file.filename} to collection '{collection_name}'."}

    except Exception as e:
        print(f"Error during file upload: {e}")
        print(f"Error details: {repr(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during file upload: {str(e)}"
        )