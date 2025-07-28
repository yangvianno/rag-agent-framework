# src/rag_agent_framework/ingestion/cad_parser.py

import os
import steputils
from pathlib import Path

def parse_step_file(file_path: str) -> dict:
    """
        Parses a .STEP file using steputils to extract the product/assembly hierarchy.

        Args:
            file_path: The path to the .STEP file

        Returns:
            A dictionary containing structured data about the model
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"STEP file not found at {file_path}")
    
    print(f"Parsing STEP file with steutils: {os.path.basename(file_path)}...")

    # Load the STEP file
    cad_file = steputils.load(file_path)

    parts = []
    # A STEP file can have multiple assemblies, so we iterate
    for assembly in cad_file.assemblies:
        # This is a simple representation,a real parser would traverse the tree
        part_name = assembly.name if assembly.name else f"Unnamed_Part_in_{Path(file_path).name}"
    
        # NOTE: steputils doesn't do geometric calculations like volume, here, only extracting the structural info
        part_data = {
            "part_id": part_name,
            "volume": 0.0, # Placeholder
            "properties_text": f"Part: {part_name} from source file {Path(file_path).name}"
        }
        parts.append(part_data)
    

    if not parts:
        # Handles cases where there might not be a defined assembly
        parts.append({
            "part_id": Path(file_path).stem,
            "volume": 0.0,
            "properties_text": f"Part: {Path(file_path).stem} from source file {Path(file_path).name}"
        })

    print(f"Successfully extracted data for {len(parts)} part(s)")

    return {
        "filename": os.path.basename(file_path),
        "parts": parts
    }

    