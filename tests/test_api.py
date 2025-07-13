# tests/test_api.py

from fastapi.testclient import TestClient
from rag_agent_framework.api.server import app

# Create a client to interact with app in tests
client = TestClient(app)

def teset_health_check():
    """ Tests if the /health endpoint returns a 200 OK status and the correct JSON response"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_read_main_docs():
    """Tests if the main documentation page loads correctly"""
    response = client.get("/docs")
    assert response.status_code == 200