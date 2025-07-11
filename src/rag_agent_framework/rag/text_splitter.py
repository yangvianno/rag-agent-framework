# src/rag_agent_framework/rag/text_splitter.py

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from rag_agent_framework.core.config import RETRIEVER_CFG


"""
Breaks each Document into smaller chunks for embedding, using settings from the central configuration file
"""

def split_documents(documents: list[Document]) -> list[Document]:
    chunk_size = RETRIEVER_CFG.get("chunk_size", 1000)
    chunk_overlap = RETRIEVER_CFG.get("chunk_overlap", 200)
    print(f"Splitting documents with chunk_size={chunk_size} and chunk_overlap={chunk_overlap}")

    
    splitter = RecursiveCharacterTextSplitter(chunk_size = chunk_size,
                                             chunk_overlap = chunk_overlap,
                                             length_function = len)
    
    return splitter.split_documents(documents)