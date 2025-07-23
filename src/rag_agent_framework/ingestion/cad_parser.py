# src/rag_agent_framework/ingestion/cad_parser.py

import os
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TopAbs      import TopAbs_SOLID
from OCC.Core.GProp       import GProp_GProps
from OCC.Core.BRepGProp   import brepgprop_VolumeProperties

def parse_step_file(file_path: str) -> dict:
    """
        Parses a .STEP file to extract part hierarchy and properties

        Args:
            file_path: the path to the .STEP file

        Returns:
            A dictionary containing structured data about the model
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"STEP file not found at {file_path}")
    
    print(f"Parsing STEP file: {os.path.basename(file_path)}...")

    reader = STEPControl_Reader()
    status = reader.ReadFile(file_path)
    if not status:
        raise ValueError(f"Failed to read STEP file: {file_path}")
    reader.TransferRoots()
    shape = reader.OneShape()

    # -- Data Extraction Lofic --
    parts = []
    # In a real scenario would traverse the assembly tree. For now we'll treat each solid as a part
    # A more complex explorer would be a needed for assemblies

    # This is a placeholder for a more shape explorer
    # For,now, we assume a single part file for simplicity
    props = GProp_GProps()
    brepgprop_VolumeProperties(shape, props)

    part_data = {
        "part_id": os.path.basename(file_path),
        "volume": props.Mass(),  # In OpenCASCADE, Mass() gives volume if density is 1
        "properties_text": f"Part: {os.path.basename(file_path)}, Volume: {props.Mass():.2f} mm^3"
    }
    parts.append(part_data)

    print(f"Successfully extracted data for {len(parts)} part(s).")

    return {
        "filename": os.path.basename(file_path),
        "parts": parts
    }