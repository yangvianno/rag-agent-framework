# src/rag_agent_framework/utils/db_connections.py -- utility file for managing clients to avoid re-writing database connection code

import os
from qdrant_client import QdrantClient
from neo4j         import GraphDatabase, Driver
from dotenv        import load_dotenv
load_dotenv()

class DatabaseConnections:
    """A singleton class to manage database connections"""
    _qdrant_client = None
    _neo4j_driver  = None

    @classmethod
    def get_qdrant_client(cls) -> QdrantClient:
        if cls._qdrant_client is None:
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            print(f"Initializing qdrant client at {qdrant_url}")
            cls._qdrant_client = QdrantClient(url= qdrant_url)
        return cls._qdrant_client
    
    @classmethod
    def get_neo4j_driver(cls) -> Driver:
        if cls._neo4j_driver is None:
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            print(f"Initializing Neo4j driver at {neo4j_uri}")
            cls._neo4j_driver = GraphDatabase(url= neo4j_uri)
        return cls._neo4j_driver
    
    # Only Neo4j client has an explicit close method
    @classmethod
    def close_connections(cls):
        if cls._neo4j_driver:
            print("Closing Neo4j driver.")
            cls._neo4j_driver.close()
            cls._neo4j_driver = None

# Example of how to use it:
# db_manager = DatabaseConnections()
# qdrant = db_manager.get_qdrant_client()
# neo4j  = db_manager.get_neo4j_driver()
# db_manager.close_connections()
