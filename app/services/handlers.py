
import re
from typing import Any
import uuid

from dotenv import load_dotenv
from fastapi import Request
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload

from app.prompts.single_doc import singleDocPrompt
from app.prompts.system_prompt import CHAT_PROMPT, RECALL_PROMPT
from app.rag.resolve_doc_name import resolve_doc
from app.schema.conversation_schema import Conversation
from app.schema.document_schema import Document
from app.services.embedding.embedding_service import Embedding
from app.services.message_service import save_message
from app.services.rag.rag_llm_service import RAG_llm
from app.services.vector.vector_service import _compare, _summarize_one, retrieved_chunks_for_compare, retrieved_grouped_document_chunks
from app.utils.common import _history_for_answer

load_dotenv()

client = AsyncOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
    )

async def handle_chat(user_query: str, history: list[dict]):

    response = await client.chat.completions.create(
        model="gemma4:e2b",
        messages=[
            {"role": "system", "content": CHAT_PROMPT},
            *_history_for_answer(user_query,chat_history=history),
            {"role": "user", "content": user_query}
        ],
    )

    return {"answer": response.choices[0].message.content, "sources": []}

async def handle_recall(user_query: str, history: list[dict]):
    if not history:
        return {"answer": "We haven't discussed anything yet.", "sources": []}

    response = await client.chat.completions.create(
        model="gemma4:e2b",
        messages=[
            {"role": "system", "content": RECALL_PROMPT},
            *_history_for_answer(user_query=user_query, chat_history=history),
            {"role": "user", "content": user_query}
        ],
    )

    return {"answer": response.choices[0].message.content, "sources": []}

async def handle_search(request: Request, user_query: str, queries: list[str], top_k: int, chat_history: list[dict], conversation_id: uuid.UUID, db: AsyncSession):
    embedding_service: Embedding = request.app.state.embedding_service

    await save_message(db, conversation_id, user_query, role="user")

    # embeddings generate
    embeddings = embedding_service.embed_chunks(chunks=queries)

    retrieved_data = await retrieved_grouped_document_chunks(request=request,queries=queries, embeddings=embeddings, conversation_id=conversation_id, top_k_qdrant=top_k)

    if not retrieved_data["chunks"]:
        return "No relevant information found in the uploaded documents."

    doc_name = retrieved_data["document_name"]
    context_text = "\n\n".join([c["text"] for c in retrieved_data["chunks"]])

    chat_history = _history_for_answer(user_query=user_query, chat_history=chat_history)

    prompt = singleDocPrompt(doc_name, context_text, chat_history, user_query=queries)

    answer = await RAG_llm(prompt)

    await save_message(db,conversation_id,content=answer,role="assistant")

    # Call your LLM model here with 'prompt'
    return {"answer": answer, "sources": []}

async def handle_compare(request: Request, db: AsyncSession, conversation_id: uuid.UUID, plan: dict, user_query: str, chat_history: list[dict]) -> dict[str, Any]:
    embedding_service = request.app.state.embedding_service

    # ---- 0. persist user message ----
    await save_message(db, conversation_id, user_query, role="user")

    # ---- 1. load available docs (only ready ones) ----
    result = await db.execute(
        select(Document).where(
            Document.conversation_id == conversation_id,
            Document.status == "UPLOADED",     # ← adjust to your enum value
        )
    )
    available_docs = result.scalars().all()

    if len(available_docs) < 2:
        return {
            "answer": "I need at least two documents to compare. "
                      "Please upload another document.",
            "sources": [],
        }

    # user-facing name = original_filename; dedupe if collisions
    name_to_doc: dict[str, Document] = {}
    for d in available_docs:
        key = d.original_filename
        if key in name_to_doc:
            # avoid silent collisions on same name
            key = f"{d.original_filename} ({str(d.id)[:8]})"
        name_to_doc[key] = d

    available_names = list(name_to_doc.keys())

    # ---- 2. resolve each side ----
    resolved_doc_ids: list[str] = []      # str(doc.id)
    resolved_names: list[str] = []        # original_filename
    ambiguous: list[tuple[str, list[str]]] = []
    not_found: list[str] = []

    for side in plan.get("sides", []):
        r = resolve_doc(side["doc"], available_names)
        if r["status"] == "ok":
            doc = name_to_doc[r["doc"]]
            resolved_doc_ids.append(str(doc.id))
            resolved_names.append(doc.original_filename)
        elif r["status"] == "ambiguous":
            ambiguous.append((side["doc"], r["candidates"]))
        else:
            not_found.append(side["doc"])

    # ---- 3. bail before retrieval ----
    if not_found:
        return {
            "answer": (
                f"I couldn't find: {', '.join(not_found)}.\n"
                f"You have: {', '.join(available_names)}"
            ),
            "sources": [],
        }

    if ambiguous:
        lines = []
        for said, cands in ambiguous:
            listing = "\n".join(f"  • {c}" for c in cands)
            lines.append(f"For '{said}', did you mean one of these?\n{listing}")
        return {
            "answer": "\n\n".join(lines) + "\n\nPlease reply with the exact names.",
            "sources": [],
        }

    # dedupe
    seen: set[str] = set()
    dedup_ids: list[str] = []
    dedup_names: list[str] = []
    for did, name in zip(resolved_doc_ids, resolved_names):
        if did not in seen:
            seen.add(did)
            dedup_ids.append(did)
            dedup_names.append(name)
    resolved_doc_ids, resolved_names = dedup_ids, dedup_names


    if len(resolved_doc_ids) == 1:
        return {
            "answer":
                f"Compare needs two documents. You mentioned "
                f"'{resolved_names[0]}'. Which second document should I "
                f"compare it with?\nYou have: {', '.join(available_names)}",
            "sources": [],
    }
    
    if len(resolved_doc_ids) == 0:
        return {
            "answer":
                f"Which two documents would you like to compare?\n"
                f"You have: {', '.join(available_names)}",
            "sources": [],
    }

    # if len(resolved_doc_ids) < 2:
    #     return {
    #         "answer": "Compare needs two documents. You mentioned "
    #                 f"'{resolved_names[0] if resolved_names else '?'}'. "
    #                 f"Which second document should I compare it with?\n"
    #                 f"You have: {', '.join(available_names)}",
    #         "sources": [],
    # }

    if len(resolved_doc_ids) > 4:
        return {
            "answer": "I can compare up to 4 documents at a time. "
                      f"Please pick 4 from: {', '.join(available_names)}",
            "sources": [],
        }

    # ---- 4. mode ----
    queries = plan.get("queries", [])
    whole_doc = not queries

    embeddings: list[list[float]] = []
    if not whole_doc:
        embeddings = embedding_service.embed_chunks(chunks=queries)

    # ---- 5. retrieve per-doc ----
    retrieved = await retrieved_chunks_for_compare(
        request=request,
        queries=queries,
        embeddings=embeddings,
        conversation_id=conversation_id,
        doc_ids=resolved_doc_ids,        # these are str(Document.id)
        whole_doc=whole_doc,
    )

    if retrieved.get("error"):
        return {"answer": retrieved["error"], "sources": []}

    docs_out = retrieved["documents"]

    # ---- 6. empty side? ----
    empties = [d["document_name"] for d in docs_out if d.get("empty")]
    if empties:
        return {
            "answer": f"No content found in: {', '.join(empties)}.",
            "sources": resolved_names,
        }

    # ---- 7. pre-summarize long docs (whole-doc mode) ----
    if whole_doc:
        for d in docs_out:
            total = sum(len(c["text"]) for c in d["chunks"])
            if total > 12000:
                summary = await _summarize_one(
                    f"Summarize this document: {d['document_name']}",
                    d["chunks"],
                )
                d["chunks"] = [{"text": summary, "rerank_score": 0.0}]

    # ---- 8. LLM ----
    answer = await _compare(
        user_query=len(queries) > 0 and queries or user_query,
        documents=docs_out,
        chat_history=chat_history,
        concept_mode=not whole_doc,
    )

    await save_message(db, conversation_id, content=answer, role="assistant")

    return {
        "answer": answer,
        "sources": [d["document_name"] for d in docs_out],
    }