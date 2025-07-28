# services/pdf-parser/app/main.py

import shutil
import tempfile
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import PlainTextResponse
from pdf_parser import parse_pdf_to_markdown  # your wrapper

app = FastAPI(title="PDF Parsing Service")

@app.post("/parse_pdf/", response_class=PlainTextResponse)
async def parse_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files accepted")
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    with tmp as f:
        shutil.copyfileobj(file.file, f)
    try:
        md = parse_pdf_to_markdown(tmp.name)
    except Exception as e:
        raise HTTPException(500, f"PDF parse failed: {e}")
    return md