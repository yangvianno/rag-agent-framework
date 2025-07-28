# services/cad-parser/app/runner.py -- a bridge between the web server and the CAD parser. Simple script to execute the parser
# if a CAD file causes the parser to crash -> only the separate subprocess will terminate -> web server logs error to user rather calling parser directly from main.py -> crash entire web service

import os, sys, json, logging

# This ensures that other modules in the same directory (like cad_parser.py) can be found.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cad_parser import parse_step_file

logging.basicConfig(
    level  = logging.INFO, 
    format = "%(asctime)s %(levelname)s: %(message)s"
)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logging.error("Invalid number of arguments. Usage: python runner.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        result = parse_step_file(file_path)
        print(json.dumps(result))           # Print the result as a JSON string to be captured by the main process
    except Exception as e:
        logging.exception(f"An error occurred while parsing {file_path}")
        sys.exit(1)