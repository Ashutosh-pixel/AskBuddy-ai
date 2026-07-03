from uuid import UUID

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.build_gpt_messages_service import build_get_messages
from app.services.conversation_service import get_conversation
from app.services.message_service import get_messages, save_message
from app.services.stream_llm_service import stream_llm


async def process_chat_stream(request: Request,message: str, conversation_id: UUID, db:Session=Depends(get_db)):
    conversation = get_conversation(db,conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    save_message(db, conversation_id, message, role="user")

    history = get_messages(db,conversation_id)

    messages = build_get_messages(history=history)

    full_response = ""

    async for chunk in stream_llm(messages):
        # browser disconnect stop llm and save pratial message in DB
        if await request.is_disconnected():
            break

        full_response += chunk

        # Immediately send chunk to client or return
        yield f"data: {chunk}\n\n"

    save_message(db,conversation_id,content=full_response,role="assistant")
