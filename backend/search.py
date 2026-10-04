from ingest import create_embedding
from qdrant_db import create_collection_if_needed, COLLECTION_NAME

MAX_RESULTS = 5


def search_documents(question):
    qdrant = create_collection_if_needed()

    question_embedding = create_embedding(question)

    results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=question_embedding,
        limit=MAX_RESULTS,
        with_payload=True,
    )

    print(f"Qdrant search results for: {question!r}")

    matching_chunks = []
    for point in results.points:
        chunk_text = point.payload["text"]
        file_name = point.payload["file_name"]
        print(f"  score={point.score:.3f}  file={file_name}  text={chunk_text[:60]!r}...")
        matching_chunks.append({"text": chunk_text, "file_name": file_name, "score": point.score})

    return matching_chunks
