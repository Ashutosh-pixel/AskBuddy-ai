import asyncio
import time
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select

from app.core.logger import logger
from app.database.connection import AsyncSession, get_db
from app.schema.conversation_schema import Conversation
from app.services.build_gpt_messages_service import build_get_messages
from app.services.conversation_service import get_conversation
from app.services.llm_service import ask_llm
from app.services.message_service import get_messages, save_message
from app.services.stream_llm_service import stream_llm
from app.utils.config import titlePrompt


async def process_chat_stream(request: Request,message: str, request_id: str, start:float, conversation_id: UUID, conversation:Conversation, db:AsyncSession=Depends(get_db)):

    await save_message(db, conversation_id, message, role="user")
    logger.info(f"[{request_id}] save user prompt in the database")

    history = await get_messages(db,conversation_id)
    logger.info(f"[{request_id}] loading history from database")

    messages = build_get_messages(history=history)
    logger.info(f"[{request_id}] build messages array")

    title_task=None
    if conversation.title is None:
        userQuestion = [
            {
                "role": "system",
                "content": titlePrompt["system"]
            },
            {
                "role": "user",
                "content": message
            }
        ]

        title_task = asyncio.create_task(
            ask_llm(messages=userQuestion)
        )

    full_response = ""

    logger.info(f"[{request_id}] calling LLM")

    try:
        async for chunk in stream_llm(messages):
            # browser disconnect stop llm and save pratial message in DB
            if await request.is_disconnected():
                logger.warning(f"[{request_id}] client disconnected")
                break

            full_response += chunk

            # Immediately send chunk to client or return
            yield f"data: {chunk}\n\n"

        logger.info(f"[{request_id}] stream completed")

    except asyncio.CancelledError:
        logger.warning(f"[{request_id}] client disconnected")
        raise

    finally:
        logger.info(f"[{request_id}] save LLM prompt in the database")
        await save_message(db,conversation_id,content=full_response,role="assistant")
        duration = time.perf_counter()-start
        logger.info(f"[{request_id}] completed in {duration:.2f}s")

        if conversation.title is None:
            try:
                if title_task:
                    title = await title_task
                    logger.info(f"[{request_id}] title is created")

                    print(f"TITLE= {title}")

                    # save title in db
                    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
                    resp = result.scalar_one()
                    resp.title = title
                    await db.commit()
                    logger.info(f"[{request_id}] title saved in DB")

            except Exception:
                logger.warning(f"[{request_id}] title generation failed")
