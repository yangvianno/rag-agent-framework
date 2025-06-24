# src/rag_agent_framework/rag/data_loader.py

from pathlib import Path
from langchain.document_loaders import PyPDFLoader, WebBaseLoader
from langchain.schema import Document

"""
    Load a PDF from disk or fetch & parse text from a URL.
    Returns a list of LangChain Document objects.
"""

def load_documents(source: str) -> list[Document]:
    if Path(source).is_file(): loader = PyPDFLoader(str(source))    # If it's a local file
    else: loader = WebBaseLoader(source)

    return loader.load()