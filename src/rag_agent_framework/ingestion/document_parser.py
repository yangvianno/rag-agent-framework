# scripts/document_parser.py

from markitdown import Markitdown
import os

def parse_document(file_path: str) -> str:
    """Uses MarkitDown to convert a variety of document types into clean Markdown text
       Args: file_path
       Returns: a string containing the document's content as Markdown"""
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at {file_path}")
    
    print( f"Parsing document: {os.path.basename(file_path)} with MarkitDown...")

    converter = Markitdown(file_path)
    markdown_content = str(converter)

    print(f"Successfully converted {os.path.basename(file_path)} to Markdown.")
    return markdown_content
