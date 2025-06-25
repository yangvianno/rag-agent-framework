# test_qdrant_connection.py
from qdrant_client import QdrantClient, models

QDRANT_URL = "http://localhost:6333"
TEST_COLLECTION_NAME = "test_connection"

print(f"--- Attempting to connect to Qdrant at {QDRANT_URL} ---")

try:
    # 1. Create a client instance
    client = QdrantClient(url=QDRANT_URL)
    print("Client created successfully.")

    # 2. A simple operation to verify the connection is live
    client.recreate_collection(
        collection_name=TEST_COLLECTION_NAME,
        vectors_config=models.VectorParams(size=4, distance=models.Distance.DOT),
    )
    print(f"Successfully created or connected to collection '{TEST_COLLECTION_NAME}'.")

    # 3. Get collection info
    collection_info = client.get_collection(collection_name=TEST_COLLECTION_NAME)
    print("\n✅ SUCCESS: Successfully connected to Qdrant and performed operations.")
    print("Collection Info:", collection_info)

except Exception as e:
    print(f"\n❌ FAILED: Could not connect to or operate with Qdrant.")
    print(f"Error details: {e}")
    print("\nTroubleshooting:")
    print("1. Is the Qdrant Docker container running? (Check with 'docker ps')")
    print("2. Is another process using port 6333?")
    print("3. Is a firewall, VPN, or proxy on your Mac interfering with the connection to localhost?")