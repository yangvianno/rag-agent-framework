# src/rag_agent_framework/rag/rag_chain.py

import os 
from langchain_openai import ChatOpenAI
from langchain_community.chat_models.ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


from rag_agent_framework.core.config import LLM_CFG, OPENAI_API_KEY, OLLAMA_URL, RETRIEVER_K
from rag_agent_framework.rag.vector_store import get_vector_store

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
                         base_url = OLLAMA_URL)
        
    # Get the vector store and retriever
    vector_store = get_vector_store(collection_name=collection_name, url=url)
    retriever = vector_store.as_retriever(search_kwargs={"k": RETRIEVER_K})

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