# services/cad-parser/app/main.py -- FastAPI Web Server listens fo requests, handles file uploads, and sends back responses
# 1. A user sends a CAD file to /parse_cad/ endpoint in main.py
# 2. The server saves the uploaded file to a temporary location on the disk
# 3. The server executes runner.py as a new process, passing the path to the temporary file as argument
#   a. The runner.py script imports the parse_step_file function from cad_parser.py and calls it with the file_path
#   b. Once parsing complete, runner.py takes a dict of results -> JSON string -> prints it to its standard output
# 4. The main.py captures the (JSON string) from runner.py -> sends it as the HTTP response
#   c. The temporary file is deleted

## Run the Test
# docker compose up -d --build
# curl -X POST -F "file=@services/cad-parser/test/Part2.STEP" http://localhost:8001/parse_cad/

import os, sys, json, shutil, tempfile, logging, subprocess
from fastapi           import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level  = os.getenv("LOG_LEVEL", "INFO"), 
    format = "%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("cad-parser")

app = FastAPI(title = "CAD Parsing Service")

@app.post("/parse_cad/")
def parse_cad_endpoint(file: UploadFile = File(...)):
    """
        Parses a CAD file by running the core logic in an isolated subprocess for maximum stability.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".step", ".stp", ".iges", ".igs"):
        raise HTTPException(status_code=400, detail="Unsupported CAD format")

    # Create a temporary file to store the upload
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_file_path = tmp.name

    try:
        # Prepare the command to run the parser script in a separate process
        # This uses the same Python executable that the app is running in
        runner_path = os.path.join(os.path.dirname(__file__), "runner.py")      # Find the dir of main.py located then create full path to runner.py which in the same dir so program find its helper script
        command = [sys.executable, runner_path, temp_file_path]                 # ["python", "/path/to/runner.py", "/path/to/your/temp_file.step"]
        logger.info(f"Running command: {' '.join(command)}")

        # Execute the command
        process = subprocess.run(
            command,
            check          = True,
            capture_output = True,
            text           = True,  # decoded as string rather raw bytes
            timeout        = 120    # 2-minute timeout
        )

        # The JSON output from the script is in process.stdout
        logger.info("Subprocess executed successfully.")
        result = json.loads(process.stdout)
        
    except subprocess.CalledProcessError as e:
        # This error is raised if the script exits with an error
        logger.error(f"The parsing script failed with exit code {e.returncode}.")
        logger.error(f"Stderr: {e.stderr}")
        raise HTTPException(status_code=500, detail=f"Failed to parse CAD file. See server logs for details.")
    except subprocess.TimeoutExpired:
        logger.error("The parsing script timed out.")
        raise HTTPException(status_code=500, detail="Parsing process timed out.")
    except Exception as e:
        logger.exception("An unexpected error occurred while managing the subprocess.")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")
    finally:
        # Crucially, ensure the temporary file is always deleted
        os.unlink(temp_file_path)

    return JSONResponse(content=result)