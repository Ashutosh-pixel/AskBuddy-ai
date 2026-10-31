
import uuid

from dotenv import load_dotenv
from fastapi import Request
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload

from app.prompts.single_doc import singleDocPrompt
from app.prompts.system_prompt import CHAT_PROMPT, RECALL_PROMPT
from app.schema.conversation_schema import Conversation
from app.schema.document_schema import Document
from app.services.embedding.embedding_service import Embedding
from app.services.message_service import save_message
from app.services.rag.rag_llm_service import RAG_llm
from app.services.vector.vector_service import retrieved_grouped_document_chunks

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
            *history[-4:],
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
            *history[-4:],
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

    prompt = singleDocPrompt(doc_name, context_text, chat_history, user_query=queries)

    answer = await RAG_llm(prompt)

    await save_message(db,conversation_id,content=answer,role="assistant")

    # Call your LLM model here with 'prompt'
    return {"answer": answer, "sources": []}