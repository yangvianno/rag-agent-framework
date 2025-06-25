# src/rag_agent_framework/rag/text_splitter.py

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

"""
Breaks each Document into smaller chunks for embedding.
"""

def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size = 1000,
                                             chunk_overlap = 200,
                                             length_function = len)
    
    return splitter.split_documents(documents)