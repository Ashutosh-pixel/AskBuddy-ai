from collections import defaultdict
from typing import Any, Dict
from uuid import UUID, uuid4

from fastapi import Request
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
    query: str,
    embedding: list[float],
    conversation_id: UUID,
    top_k_qdrant: int = 20,
    top_k_final: int = 3
) -> Dict[str, Any]:
    """
    Retrieves chunks for a conversation, reranks them, and isolates chunks 
    belonging strictly to the single most relevant document to prevent context bleeding.
    """
    
    # 1. Filter Qdrant by conversation_id and fetch Top-K chunks
    response = await client.query_points(
        collection_name=os.getenv("COLLECTION_NAME"),
        query=embedding,  # Your BGE vector generation function
        query_filter= Filter(
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

    search_results = response.points
    
    if not search_results:
        return {"winning_doc_id": None, "chunks": []}

    # 2. Prepare pairs for Cross-Encoder Reranking
    pairs = [hit.payload["text"] for hit in search_results]
    rerank_scores = request.app.state.reranker.rerank(query=query, chunks=pairs)
    
    # Attach rerank score back to the hit standard payloads
    scored_hits = []
    for hit, score in zip(search_results, rerank_scores):
        scored_hits.append({
            "document_id": hit.payload["document_id"],
            "document_name": hit.payload.get("document_name", "Unknown"),
            "text": hit.payload["text"],
            "rerank_score": float(score)
        })


    # 3. Group hits by doc_id
    grouped_docs = defaultdict(list)
    for hit in scored_hits:
        grouped_docs[hit["document_id"]].append(hit)


    # 4. Identify the winning document based on the highest individual chunk score
    winning_doc_id = max(
        grouped_docs.keys(),
        key=lambda d_id: max(chunk["rerank_score"] for chunk in grouped_docs[d_id])
    )

    # 5. Extract and order the top-K chunks strictly from the winning document
    winning_doc_chunks = grouped_docs[winning_doc_id]
    winning_doc_chunks.sort(key=lambda x: x["rerank_score"], reverse=True)
    
    final_chunks = winning_doc_chunks[:top_k_final]

    return {
        "winning_doc_id": winning_doc_id,
        "document_name": final_chunks[0]["document_name"],
        "chunks": final_chunks
    }