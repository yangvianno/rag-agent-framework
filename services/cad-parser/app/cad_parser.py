# services/cad-parser/app/main.py -- Engine of application, contains the logic to actually read & interpret the geometric data from STEP files
import logging
from OCC.Core.STEPControl import STEPControl_Reader             # Reads STEP files into OpenCASCADE shapes
from OCC.Core.TopAbs      import TopAbs_SOLID                   # A type constant, used to filter for solid objects
from OCC.Core.GProp       import GProp_GProps                   # Stores geometric properties like volume, center off mass, etc.
from OCC.Core.BRepGProp   import brepgprop_VolumeProperties     # Calculates volume from a 3D shape
from OCC.Core.TopExp      import TopExp_Explorer                # Allows to loop through sub-shapes (e.g., solids) in a model
from OCC.Core.BRep        import BRep_Tool                      # Toolbox for working with shapes (e.g., triangulation, points)
from OCC.Core.TopoDS      import topods                         # Converts a generic shape to a more specific one (like Solid)
from OCC.Core.IFSelect    import IFSelect_RetDone               # Constant indicating a successful file-read in the IFSelect reader
from OCC.Core.Bnd         import Bnd_Box                        # Axis-aligned bounding box container for computing shape extents
from OCC.Core.BRepBndLib  import brepbndlib_Add                 # Utility to add a shape's bounds into a Bnd_Box

logger = logging.getLogger("cad-parser")

def parse_step_file(file_path: str) -> dict:
    """
        Parses a .STEP file to extract geometric properties and part hierarchy
        Returns a JSON-serializable dict.    
    """
    logger.info(f"--- Starting to parse file: {file_path} ---")
    reader = STEPControl_Reader()
    logger.info("STEPControl_Reader initialized.")
    status = reader.ReadFile(file_path)
    if status != IFSelect_RetDone:
        logger.error("Failed to read STEP file.")
        raise ValueError("Failed to read STEP file")
    logger.info("Successfully read file.")

    # Transfering shape data
    try:
        reader.TransferRoots()      # Processes the loaded file into usable shapes
        logger.info("Successfully transferred roots.")
        shape = reader.OneShape()   # Givees the top-level shape (the entire model)
        logger.info("Successfully got top-level shape.")
    except Exception as e:
        logger.error(f"Error processing STEP file shape transfer: {e}")
        raise ValueError(f"Error processing STEP file: {str(e)}")
    
    if shape is None or shape.IsNull():
        logger.info("Shape is null after transfer.")
        raise ValueError("Failed to extract a valid shape from the file.")

    # Volume computation (1)
    properties = GProp_GProps()                     # Container for properties (like volume, center of gravity)
    brepgprop_VolumeProperties(shape, properties)   # Fills properties with info
    volume = properties.Mass()                      # Returns volume of the entire shape
    logger.info(f"Calculated total volume: {volume}")

    ## Build a simple hierarchy: find solids and compute bounding boxes
    # Exploring sub-shapes (solids)
    hierarchy = []                                  # Store info about individual parts
    explorer = TopExp_Explorer(shape, TopAbs_SOLID) # Used to walk through all solids in the shape
    logger.info("Initialized solid explorer.")

    # Loop through solids
    i = 0
    while explorer.More():                          # Checks if there's another solid
        i += 1
        logger.info(f"Processing solid {i}")
        solid = topods.Solid(explorer.Current())    # Converts (gives the current solid-generic type) into a usable Solid object

        # Computes each individual solid volume - same as (1)
        solid_properties = GProp_GProps()
        brepgprop_VolumeProperties(solid, solid_properties)
        volume_i = solid_properties.Mass()

        # Bounding box placeholder (TODO)
        box = Bnd_Box()
        brepbndlib_Add(solid, box)
        xmin, ymin, zmin, xmax, ymax, zmax = box.Get()
        hierarchy.append({
            "id":     f"solid_{len(hierarchy)}",
            "volume": volume_i,
            "bbox":   [xmin, ymin, zmin, xmax, ymax, zmax],
        })
        logger.info(f"Finished processing solid {i} with volume {volume_i}")
        explorer.Next()

    logger.info(f"--- Successfully finished parsing. Found {len(hierarchy)} solids. ---")

    return {
        "volume":     volume,
        "part_count": len(hierarchy),
        "hierarchy": hierarchy,
        # extend with wall_thickness, feature_counts, etc.
    }