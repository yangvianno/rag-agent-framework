# services/pdf-parser/app/main.py

import os, shutil, tempfile, logging
from fastapi                 import FastAPI, File, UploadFile, HTTPException
from fastapi.responses       import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic                import BaseModel
from pdf_parser              import convert_to_markdown, ParseError

# ——— Load configuration ———
MAX_UPLOAD_MB   = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
MAX_UPLOAD_SIZE = MAX_UPLOAD_MB * (1 << 20)     # in bytes: 1024 * 1024

# ——— Logging Setup ———
logging.basicConfig(
    level  = os.getenv("LOG_LEVEL", "INFO"),
    format = "%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("pdf-parser")

# ——— FastAPI App ———
app = FastAPI(
    title       = "PDF Parsing Service",
    version     = "1.0.0",
    description = "Uploads PDF file and returns structured Markdown for downstream processing"
)

# Enable CORS if call this from a browser-based UI
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["POST"],
    allow_headers = ["*"]
)

# ——— Pydantic Models ———
class ParsePDFResponse(BaseModel):
    markdown_content: str

# ——— Endpoints ———
@app.post("/parse_pdf/", response_model=ParsePDFResponse, summary="Parse a PDF to Markdown")
async def parse_pdf_endpoint(file: UploadFile = File(...)):
    # 1. Validate  file tpe
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    # 2. Enfore a configurable size limit
    chunk  = await file.read(MAX_UPLOAD_SIZE + 1)       # read the file into chunk (binary data) + extra 1 byte
    if len(chunk) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    await file.seek(0)      # Moves the file pointer back to the beginning if size no exceeds

    # 3. Write to a safe temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name

    # 4. Invoke parser
    try:
        logger.info(f"Parsing {file.filename} → {temp_path}")
        
        markdown_text = convert_to_markdown(temp_path)
        logger.info(f"Parse successful !")
        
        return ParsePDFResponse(markdown_content = markdown_text)
    
    except ParseError as pe:
        logger.error("! Parsing failed !", exc_info = pe)
        raise HTTPException(status_code=422, detail=f"Internal server error: {pe}")
    except Exception as e:
        logger.exception("Unexpected error during parsing")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            logger.warning(f"Failed to delete temp file {temp_path}")