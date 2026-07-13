from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.chat_model import ChatResponse
from app.services.build_gpt_messages_service import build_get_messages
from app.services.conversation_service import get_conversation
from app.services.message_service import get_messages, save_message
from app.services.llm_service import ask_llm


async def process_chat(request: str, conversation_id: UUID, db: Session=Depends(get_db)):
    # 1
    conversation = get_conversation(db, conversation_id)

    if conversation is None:
        return {}

    # 2
    save_message(db, conversation_id,content=request, role="user")

    # 3
    history = get_messages(db, conversation_id)

    # 4
    messages = build_get_messages(history=history)

    # 5
    answer = await ask_llm(messages)

    # 6
    save_message(db, conversation_id,content=answer, role="assistant")

    # 7
    return ChatResponse(answer=answer)
