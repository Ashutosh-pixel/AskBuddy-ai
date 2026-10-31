from collections import defaultdict
from typing import Any, Dict
from uuid import UUID, uuid4

from fastapi import Request
from qdrant_client import models
from qdrant_client.models import FieldCondition, MatchValue, PointStruct, Filter
from app.services.retrieval.reranker import Reranker
from app.services.vector.qdrant_connection import client
import os

async def store_embeddings(user_id: UUID, document_id: UUID, conversation_id: UUID, document_name:str, chunks: list[str], embeddings: list[list[float]]):

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
                "conversation_id": str(conversation_id),
                "document_name": document_name,
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

    # for chunk in chunks:
    #     print(f"{chunk}\n")

    reranker = request.app.state.reranker

    reranked = reranker.rerank(query=query, chunks=chunks, top_k=3)

    return "\n\n".join([result["text"] for result in reranked])



async def retrieved_grouped_document_chunks(
    request: Request,
    queries: list[str],
    embeddings: list[list[float]],
    conversation_id: UUID,
    top_k_qdrant: int = 20,
    top_k_final: int = 3
) -> Dict[str, Any]:

    # 1. Batch Qdrant search
    batch_requests = [
        models.QueryRequest(
            query=embedding,
            filter=Filter(
                must=[
                    FieldCondition(
                        key="conversation_id",
                        match=MatchValue(value=str(conversation_id))
                    )
                ]
            ),
            with_payload=True,
            limit=top_k_qdrant
        )
        for embedding in embeddings
    ]

    response = await client.query_batch_points(
        collection_name=os.getenv("COLLECTION_NAME"),
        requests=batch_requests
    )

    # 2. Flatten and deduplicate
    unique_hits = {}

    for query_response in response:
        for hit in query_response.points:
            unique_hits[str(hit.id)] = hit

    search_results = list(unique_hits.values())

    if not search_results:
        return {"winning_doc_id": None, "chunks": []}

    # 3. Rerank
    chunks = [hit.payload["text"] for hit in search_results]

    rerank_scores = request.app.state.reranker.rerank(
        queries=queries,
        chunks=chunks
    )

    # 4. Attach scores
    scored_hits = []

    for hit, score in zip(search_results, rerank_scores):
        scored_hits.append({
            "document_id": hit.payload["document_id"],
            "document_name": hit.payload.get("document_name", "Unknown"),
            "text": hit.payload["text"],
            "rerank_score": float(score)
        })

    # 5. Group by document
    grouped_docs = defaultdict(list)

    for hit in scored_hits:
        grouped_docs[hit["document_id"]].append(hit)

    # 6. Identify winning document
    winning_doc_id = max(
        grouped_docs,
        key=lambda doc_id: max(
            chunk["rerank_score"]
            for chunk in grouped_docs[doc_id]
        )
    )

    # 7. Select top chunks
    winning_doc_chunks = sorted(
        grouped_docs[winning_doc_id],
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    final_chunks = winning_doc_chunks[:top_k_final]

    return {
        "winning_doc_id": winning_doc_id,
        "document_name": final_chunks[0]["document_name"],
        "chunks": final_chunks
    }
