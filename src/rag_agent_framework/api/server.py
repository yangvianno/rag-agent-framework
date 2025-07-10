# src/rag_agent_framework/api/server.py -- The main FastAPI server, adapting the logic from chat.py

from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional
from fastapi.concurrency import run_in_threadpool # For running sync code in async endpoints

from rag_agent_framework.agents.crew import agent_crew
from rag_agent_framework.rag.memory  import MemoryStore, get_summarizer
from rag_agent_framework.core.config import AGENT_CFG

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