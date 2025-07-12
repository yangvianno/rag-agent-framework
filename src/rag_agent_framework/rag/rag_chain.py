# src/rag_agent_framework/rag/rag_chain.py

import os 
from qdrant_client import QdrantClient, models
from langchain_openai import ChatOpenAI
from langchain_community.chat_models.ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


from rag_agent_framework.core.config import LLM_CFG, OPENAI_API_KEY, OLLAMA_URL, RETRIEVER_CFG
from rag_agent_framework.rag.vector_store import get_vector_store, get_embedder

### This template is the instruction for the LLM.
RAG_PROMPT_TEMPLATE = """
        CONTEXT:
        {context}

        QUESTION:
        {question}

        Answer the question based only on the provided context.
"""

# Builds and returns a modern RAG chain using LangChain Expression Language (LCEL)
def get_rag_chain(collection_name: str, url: str):

    # Instantiate the LLM based on config (inside te function)
    if LLM_CFG["default"] == "openai":
        llm = ChatOpenAI(model = LLM_CFG["openai"]["chat_model"],
                         openai_api_key = OPENAI_API_KEY)
    else:
        llm = ChatOllama(model = LLM_CFG["ollama"]["chat_model"],
                         base_url = OLLAMA_URL,
                         request_timeout = 300)
        
    
    # --- START: ADDED CODE TO CREATE COLLECTION ---
    # This logic ensures the collection exists before trying to use it.
    client = QdrantClient(url=url)
    try:
        client.get_collection(collection_name=collection_name)
        print(f"Collection '{collection_name}' already exists.")
    except Exception:
        print(f"Collection '{collection_name}' not found. Creating new collection.")
        embedder = get_embedder()
        vector_size = len(embedder.embed_query("test query"))
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
        )
        print(f"Successfully created collection '{collection_name}'.")
    # --- END: ADDED CODE ---
    
    
    # Get the vector store and retriever
    vector_store = get_vector_store(collection_name=collection_name, url=url)
    retriever = vector_store.as_retriever(search_kwargs={"k": RETRIEVER_CFG.get("k", 4)})

    # Create the prompt template
    prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)

    # Build RAG chain using LCEL | pipe operator
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain