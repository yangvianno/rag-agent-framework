# src/rag_agent_framework/tools/rag_tool.py -- RSG Tools for Agents use decorator @tool to wrap Python function into tool that AI agent can understand
# query.py is designed for human use vs rag_tool.py designed as API for the AI Agent, and we can add more tools later specialized for AI Agent 

import os
from crewai_tools import tool
from rag_agent_framework.rag.rag_chain import get_rag_chain


@tool("Document Knowledge Base Tool")
def rag_tool(question: str) -> str:
    """
    Searches and returns relevant information from the document knowledge base.
    Use this tool to answer questions about the contents of the ingested document
    """
    qdrant_url = os.getenv("QDRANT_URL")
    
    if not qdrant_url: raise ValueError("QDRANT_URL environment variable not set.")

    # Get the RAG chain (builds retrieval, generation pipeline) - for rag_tool to execute that pipeline given the question
    rag_chain = get_rag_chain(collection_name = "my_rag_chain", url = qdrant_url)

    # Invoke the chain with the questions
    result = rag_chain.invoke(question)

    return result

    