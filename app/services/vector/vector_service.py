from uuid import UUID, uuid4

from fastapi import Request
from qdrant_client.models import FieldCondition, MatchValue, PointStruct, Filter
from app.services.retrieval.reranker import Reranker
from app.services.vector.qdrant_connection import client
import os

async def store_embeddings(user_id: UUID, document_id: UUID, chunks: list[str], embeddings: list[list[float]]):

    if len(chunks) != len(embeddings):
        raise ValueError("Chunks and embeddings count must match")

    merge = zip(chunks,embeddings)

    points=[]

    for index, (chunk, embedding) in enumerate(merge):
        point=PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload={
                "user_id": str(user_id),
                "document_id": str(document_id),
                "chunk_index": index,
                "text": chunk
            }
        )

        points.append(point)

    await client.upsert(collection_name=os.getenv("COLLECTION_NAME"),points=points)

async def similarity_search(request: Request, user_id: UUID, query:str, embedding: list[float], top_k: int):
    response= await client.query_points(
        collection_name=os.getenv("COLLECTION_NAME"),
        query=embedding,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=str(user_id))
                )
            ]
        ),
        with_payload=True,
        limit=top_k,
    )

    chunks=[]

    for point in response.points:
        chunks.append(point.payload["text"])

    reranker = request.app.state.reranker

    reranked = reranker.rerank(query=query, chunks=chunks, top_k=3)

    return "\n\n".join([result["text"] for result in reranked])