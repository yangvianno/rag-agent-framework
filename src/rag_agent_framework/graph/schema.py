# src/rag_agent_framework/graph/schema.py

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")

def define_schema(driver):
    """
        Defines uniqueness constraints for the medical device knowledge graph.
        This ensures data integrity by preventing duplicate nodes for the same entity.
        Running this multiple times is safe (idempotent)
    """

    
    with driver.session() as session:
        print("Defining graph schema: Applying uniqueness constraints...")
        
        # Constraint for Parts: ensures each part has a unique ID
        session.run("""CREATE CONSTRAINT part_id_unique IF NOT EXISTS 
                       FOR (p:Part) REQUIRE p.part_id IS UNIQUE""")
        print("  - Constraint 'part_id_unique' ensured for (:Part).")

        # Constraint for Materials: ensures each material name is unique
        session.run("""CREATE CONSTRAINT material_name_unique IF NOT EXISTS
                       FOR (m:Material) REQUIRE m.name IS UNIQUE""")
        print("  - Constraint 'material_name_unique' ensured for (:Material).")

        # Constraint for Standards: ensures each standard ID is unique (e.g., 'ISO 10993')
        session.run("""CREATE CONSTRAINT standard_id_unique IF NOT EXISTS 
                       FOR (s:Standard) REQUIRE s:id IS UNIQUE""")
        print("  - Constraint 'standard_id_unique' ensured for (:Standard).")
        
        # Generic constraints for Documents: ensures each document is unique by its source path
        session.run("""CREATE CONSTRAINT document_path_unique IF NOT EXISTS
                       FOR (d:Document) REQUIRE d.source_path IS UNIQUE""")
        print("  - Constraint 'document_path_unique' ensured for (:Document).")
    
        print("\nSchema definition complete.")

def main():
    """Main function to connect to Neo4j and apply the schema"""
    try:
        # Use auth=None as configured in docker-compose.yml for local development
        driver = GraphDatabase.driver(NEO4J_URI, auth=None )
        driver.verify_connectivity()
        print(f"Connection to Neo4j closed.")
    except Exception as e:
        print(f"Failed to connect to Neo4j or define schema: {e}")

if __name__ == "__main__":
    main()