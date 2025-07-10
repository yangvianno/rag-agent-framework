# src/rag_agent_framework/utils/path_fix.py

import sys
from pathlib import Path

# This script ensures the 'src' directory is on the Python path.
# It allows scripts in the 'scripts/' folder to import modules from 'src/'
# as if they were run from the project root.

# Navigate up from this file's location (src/rag_agent_framework/utils) to the project root
project_root = Path(__file__).resolve().parents[3]
src_path = project_root / "src"

if not src_path.exists():
    raise FileNotFoundError(f"The 'src' folder was not found at the expected path: {src_path}")

# Add the 'src' directory to the Python path if it's not already there
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))