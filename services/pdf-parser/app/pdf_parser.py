# services/pdf-parser/app/pdf_parser.py

from markitdown import Document

def parse_pdf_to_markdown(path: str) -> str:
    doc = Document(path)
    # you can choose render_markdown() or render_html()
    return doc.render_markdown()