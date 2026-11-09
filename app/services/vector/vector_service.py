from collections import defaultdict
from typing import Any, Dict
from uuid import UUID, uuid4

from fastapi import Request
from groq import AsyncGroq
from qdrant_client import models
from qdrant_client.models import FieldCondition, MatchAny, MatchValue, PointStruct, Filter
from app.services.retrieval.reranker import Reranker
from app.services.vector.qdrant_connection import client
from app.utils.common import _history_for_answer
import os

OpenAIclient = AsyncGroq(
    api_key=os.getenv("GROQ_API_KEY")
)

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



async def retrieved_grouped_document_chunks(request: Request, queries: list[str], embeddings: list[list[float]], conversation_id: UUID, doc_ids: list[str] | None = None, top_k_qdrant: int = 20, top_k_final: int = 3) -> Dict[str, Any]:

    must=[
        FieldCondition(
            key="conversation_id",
            match=MatchValue(value=str(conversation_id))
        )
    ]

    if doc_ids:
        must.append(
            FieldCondition(
                    key="document_id",
                    match=MatchAny(any=doc_ids)
        ))

    # 1. Batch Qdrant search
    batch_requests = [
        models.QueryRequest(
            query=embedding,
            filter=Filter(
                must=must
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


async def retrieved_chunks_for_compare(
    request: Request,
    queries: list[str],
    embeddings: list[list[float]],
    conversation_id: UUID,
    doc_ids: list[str],
    top_k_qdrant: int = 20,
    top_k_per_doc: int = 4,
    whole_doc: bool = False,          # True when queries == [] (whole-doc compare)
    max_chunks_per_doc: int = 40,
) -> Dict[str, Any]:

    if not doc_ids or len(doc_ids) < 2:
        return {"documents": [], "error": "need at least 2 documents"}

    # ---- 1. filter scoped to these docs only ----
    doc_filter = Filter(
        must=[
            FieldCondition(
                key="conversation_id",
                match=MatchValue(value=str(conversation_id)),
            ),
            FieldCondition(
                key="document_id",
                match=MatchAny(any=doc_ids),
            ),
        ]
    )

    # ---- 2a. whole-doc mode: scroll ALL chunks per doc, no embedding search ----
    if whole_doc:
        per_doc_raw: dict[str, list] = {d: [] for d in doc_ids}
        for doc_id in doc_ids:
            chunks, offset = [], None
            while True:
                batch, offset = await client.scroll(
                    collection_name=os.getenv("COLLECTION_NAME"),
                    scroll_filter=Filter(must=[
                        FieldCondition(key="conversation_id",
                                       match=MatchValue(value=str(conversation_id))),
                        FieldCondition(key="document_id",
                                       match=MatchValue(value=doc_id)),
                    ]),
                    limit=100,
                    offset=offset,
                    with_payload=True,
                )
                chunks.extend(batch)
                if offset is None or len(chunks) >= max_chunks_per_doc:
                    break
            per_doc_raw[doc_id] = chunks[:max_chunks_per_doc]

    # ---- 2b. concept mode: dense search, then split by doc_id ----
    else:
        batch_requests = [
            models.QueryRequest(
                query=emb,
                filter=doc_filter,
                with_payload=True,
                limit=top_k_qdrant,
            )
            for emb in embeddings
        ]
        response = await client.query_batch_points(
            collection_name=os.getenv("COLLECTION_NAME"),
            requests=batch_requests,
        )

        # flatten + dedupe by hit id
        unique_hits = {}
        for qr in response:
            for hit in qr.points:
                unique_hits[str(hit.id)] = hit

        # split by document_id
        per_doc_raw = {d: [] for d in doc_ids}
        for hit in unique_hits.values():
            doc_id = hit.payload["document_id"]
            if doc_id in per_doc_raw:
                per_doc_raw[doc_id].append(hit)

    # ---- 3. per-doc rerank (balanced — each side treated equally) ----
    reranker = request.app.state.reranker
    per_doc_final: dict[str, list[dict]] = {}

    for doc_id, hits in per_doc_raw.items():
        if not hits:
            per_doc_final[doc_id] = []
            continue

        texts = [h.payload["text"] for h in hits]

        if whole_doc:
            # no meaningful query to rerank against — keep chronological order
            scored = list(zip(hits, [0.0] * len(hits)))
        else:
            scores = reranker.rerank(queries=queries, chunks=texts)
            scored = list(zip(hits, scores))

        ranked = sorted(scored, key=lambda x: -float(x[1]))[:top_k_per_doc]
        # print(f"ranked {ranked}")
        per_doc_final[doc_id] = [
            {
                "document_id": doc_id,
                "document_name": h.payload.get("document_name", "Unknown"),
                "text": h.payload["text"],
                "rerank_score": float(s),
            }
            for h, s in ranked
        ]

    # ---- 4. build output — one bucket per side, in caller's order ----
    documents_out = []
    for doc_id in doc_ids:
        chunks = per_doc_final[doc_id]
        documents_out.append({
            "doc_id": doc_id,
            "document_name": chunks[0]["document_name"] if chunks else "Unknown",
            "chunks": chunks,
            "empty": len(chunks) == 0,
        })

    return {"documents": documents_out, "error": None}

async def _chat(messages: list[dict], model: str = "openai/gpt-oss-20b") -> str:
    resp = await OpenAIclient.chat.completions.create(messages=messages, model=model)
    return resp.choices[0].message.content


async def _summarize_one(instruction: str, chunks: list[dict]) -> str:
    body = "\n\n".join(c["text"] for c in chunks)
    messages = [
        {"role": "system", "content":
            "Summarize the document below. Keep all names, dates, numbers, "
            "and key facts. Base it only on the provided text."},
        {"role": "user", "content": f"{instruction}\n\n{body}"},
    ]
    return await _chat(messages)


async def _compare(user_query: str, documents: list[dict], chat_history: list[dict], concept_mode: bool) -> str:
    sections = []
    for d in documents:
        body = "\n\n".join(c["text"] for c in d["chunks"])
        sections.append(f"=== DOCUMENT: {d['document_name']} ===\n{body}")
    context = "\n\n".join(sections)

    doc_names = ", ".join(f'"{d["document_name"]}"' for d in documents)

    if concept_mode:
        system = (
            "You are a document comparison assistant. The user wants to compare specific documents "
            f"({doc_names}) on ONE specific aspect named in their request.\n\n"
            "Rules:\n"
            "- Compare ONLY the aspect the user asked about. Do NOT summarize the whole documents.\n"
            "- Process the documents one at a time. For each document, extract ONLY what it says about the aspect.\n"
            "- Never merge or blend content from different documents. Attribute every fact to its source.\n"
            "- Quote or paraphrase strictly from the provided text. Do not use outside knowledge.\n"
            "- If a document does not address the aspect, write exactly: 'Not mentioned in [doc name]'. Do not invent content.\n"
            "- Cite every claim inline using [doc name] immediately after the claim.\n\n"
            "Output format (follow exactly):\n"
            "## 1. What each document says\n"
            "For each document, a short subsection headed by its name, listing only aspect-relevant points with citations.\n\n"
            "## 2. Key differences\n"
            "Bullet points highlighting genuine contrasts (or agreements) on the aspect. Each bullet must cite the docs involved.\n\n"
            "## 3. Side-by-side table\n"
            "A markdown table: | Aspect | <doc A name> | <doc B name> | ... |\n"
            "One row per sub-point of the aspect. Cells must contain only the document's own claims with citations, "
            "or 'Not mentioned' if absent. Keep cells concise."
        )
    else:
        system = (
            "You are a document comparison assistant. The user wants an overall comparison of these documents: "
            f"{doc_names}.\n\n"
            "Rules:\n"
            "- Base EVERYTHING solely on the provided text. No outside knowledge, no inference beyond the text.\n"
            "- Never attribute a claim to a document unless that document's text supports it.\n"
            "- If documents disagree, state the disagreement explicitly rather than picking one.\n"
            "- Cite every claim inline using [doc name] immediately after the claim.\n"
            "- Be concrete: prefer specific facts, figures, and named entities over vague summaries.\n\n"
            "Output format (follow exactly):\n"
            "## 1. Similarities\n"
            "Bullet points of shared content, purpose, or conclusions. Cite the supporting docs on each bullet.\n\n"
            "## 2. Differences\n"
            "Grouped by: Scope, Purpose, Content, Key facts. Use bullet points; cite docs on each bullet.\n\n"
            "## 3. Side-by-side table\n"
            "A markdown table: | Attribute | <doc A name> | <doc B name> | ... |\n"
            "Rows: Purpose, Scope, Audience, Key facts, Notable omissions. Keep cells short and cited."
        )

    messages = [
        {"role": "system", "content": system},
        *_history_for_answer(user_query=user_query, chat_history=chat_history),
        {"role": "user", "content": f"Comparison request: {user_query}\n\nDocuments to compare:\n\n{context}"},
    ]
    return await _chat(messages)