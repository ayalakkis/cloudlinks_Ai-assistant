import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

QDRANT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qdrant_data")
COLLECTION_NAME = "documents"
VECTOR_SIZE = 1536


def get_qdrant_client():
    client = QdrantClient(path=QDRANT_FOLDER)
    return client


def create_collection_if_needed():
    client = get_qdrant_client()

    existing_collections = client.get_collections().collections
    existing_names = [collection.name for collection in existing_collections]

    if COLLECTION_NAME not in existing_names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f"Created new Qdrant collection: {COLLECTION_NAME}")

    return client
