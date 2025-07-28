# services/cad-parser/test/test_parser.py
import os
import sys
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))
from cad_parser import parse_step_file

TEST_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "Part2.STEP"))

def test_parse_step_file_successfully():
    """Tests that the parser can read a valid STEP file and extract data"""
    assert os.path.exists(TEST_FILE_PATH), "Cant read"

    result = parse_step_file(TEST_FILE_PATH)

    assert isinstance(result, dict)
    assert "volume" in result
    assert "part_count" in result
    assert "hierarchy" in result

    assert isinstance(result["volume"], float)
    assert isinstance(result["part_count"], int)
    assert isinstance(result["hierarchy"], list)

    if result["part_count"] > 0:
        first_part = result["hierarchy"][0]
        assert "id" in first_part
        assert "volume" in first_part
        assert isinstance(first_part["volume"], float)

def test_parse_step_file_with_bad_path():
    """Tests that the parser raises an error for a non-existent file"""
    with pytest.raises(ValueError, match = "Failed to read STEP file"):
        parse_step_file("non_existent_file.step")
