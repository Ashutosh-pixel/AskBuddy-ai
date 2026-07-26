import time
import uuid

from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.database.connection import get_db
from app.models.chat_model import ChatRequest
from app.services.chat_service import process_chat
from fastapi import APIRouter, Depends, HTTPException, Request

from app.services.conversation_service import create_conversation, get_conversation
from app.services.process_chat_stream_service import process_chat_stream

chatRouter = APIRouter(prefix="/api")

# @chatRouter.post("/chat", response_model=ChatResponse)
# async def chatRequest(data: ChatRequest):
#     answer = await ask_llm(data.message)

#     return {
#         "answer": answer
#     }

@chatRouter.post("/conversations")
async def create_new_conversation(db: AsyncSession=Depends(get_db)):
    conversation = await create_conversation(db)

    request_id = uuid.uuid4().hex[:8]
    logger.info(f"[{request_id}] conversation created")

    return {
        "conversation_id" : conversation.id
    }

# @chatRouter.post("/conversations/{conversation_id}/message")
# def add_message(conversation_id: UUID, content:MessageCreate, db: Session=Depends(get_db)):

#     save_message(db,conversation_id,content.content,"user")

#     return True

# @chatRouter.get("/conversations/{conversation_id}/messages")
# def get_conversation_messages(conversation_id: UUID, db: Session=Depends(get_db)):

#     messages = get_messages(db, conversation_id)

#     return messages

# @chatRouter.get("/conversations/{conversation_id}")
# def get_conversation(conversation_id: UUID, db:Session=Depends(get_db)):
#     conversation = get_conversation_info(db, conversation_id)

#     return conversation

@chatRouter.post("/chat")
async def chat(message: ChatRequest, db: AsyncSession=Depends(get_db)):
    return await process_chat(message.message, message.conversation_id, db)

@chatRouter.post("/chat/stream")
async def chat_stream(request: Request,message: ChatRequest, db: AsyncSession=Depends(get_db)):
    request_id = uuid.uuid4().hex[:8]
    logger.info(f"[{request_id}] request started")

    start = time.perf_counter()

    conversation = await get_conversation(db, message.conversation_id)
    logger.info(f"[{request_id}] loading conversation from database")

    if conversation is None:
        raise HTTPException (
            status_code=404,
            detail="Conversation not found",
        )


    generator = process_chat_stream(
        request=request,
        request_id=request_id,
        start=start,
        message=message.message,
        conversation_id=message.conversation_id,
        conversation=conversation,
        db=db
    )

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # "X-Accel-Buffering": "no",   # helpful if behind nginx
    }

    return StreamingResponse(
        content=generator,
        media_type="text/event-stream",
        headers=headers
    )
