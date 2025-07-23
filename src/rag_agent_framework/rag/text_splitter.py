# src/rag_agent_framework/rag/text_splitter.py -- Reusable Component with single respoinsibility: splitting documents 

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema        import Document

"""
Breaks each Document into smaller chunks for embedding, using settings from the central configuration file
"""

def split_documents(documents: list[Document], chunk_size : int, chunk_overlap: int) -> list[Document]:
    """
    Splits a list of Documents into smaller chunks using RecursiveCharacterTextSplitter.

    Args:
        documents: List of langchain Document objects.
        chunk_size: Maximum size of each chunk.
        chunk_overlap: Number of overlapping characters between chunks.

    Returns:
        List of split Document chunks.
    """
    
    print(f"Splitting documents with chunk_size = {chunk_size} and chunk_overlap = {chunk_overlap}")

    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size      = chunk_size,
        chunk_overlap   = chunk_overlap,
        length_function = len
    )
    
    return splitter.split_documents(documents)