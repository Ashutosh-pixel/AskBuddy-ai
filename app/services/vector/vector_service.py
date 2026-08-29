from uuid import UUID, uuid4

from qdrant_client.models import FieldCondition, MatchValue, PointStruct, Filter
from app.services.vector.qdrant_connection import client
import os

async def store_embeddings(document_id:UUID, chunks:list[str], embeddings:list[list[float]]):

    if len(chunks) != len(embeddings):
        raise ValueError("Chunks and embeddings count must match")

    merge = zip(chunks,embeddings)

    points=[]

    for index, (chunk, embedding) in enumerate(merge):
        point=PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload={
                # "user_id": user_id,    use this when we will make auth system
                "document_id": str(document_id),
                "chunk_index": index,
                "text": chunk
            }
        )

        points.append(point)

    await client.upsert(collection_name=os.getenv("COLLECTION_NAME"),points=points)

async def similarity_search(document_id: UUID, embedding: list[float], top_k: int):
    response= await client.query_points(
        collection_name=os.getenv("COLLECTION_NAME"),
        query=embedding,
        query_filter=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=str(document_id)))]
            # must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]  use this when we will make auth system
        ),
        with_payload=True,
        limit=top_k
    )

    result=[]

    for point in response.points:
        result.append(point.payload["text"])

    return "\n\n".join(result)