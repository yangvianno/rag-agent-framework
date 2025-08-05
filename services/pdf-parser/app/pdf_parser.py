# services/pdf-parser/app/pdf_parser.py

from markitdown import MarkItDown

class ParseError(Exception):
    """Raised when PDF parsing fails"""
    pass

def convert_to_markdown(path: str) -> str:
    """Loads a file via Markitdown and returns its Markdown representation"""
    try:
        md = MarkItDown()
        result = md.convert(path)

        return result.text_content
    except Exception as e:
        raise ParseError(f"Error parsing PDF {path}: {e}") from e

