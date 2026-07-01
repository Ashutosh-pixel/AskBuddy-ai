from uuid import UUID

from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.chat_model import ChatRequest
from app.services.chat_service import process_chat
from fastapi import APIRouter, Depends

from app.services.conversation_service import create_conversation

chatRouter = APIRouter(prefix="/api")

# @chatRouter.post("/chat", response_model=ChatResponse)
# async def chatRequest(data: ChatRequest):
#     answer = await ask_llm(data.message)

#     return {
#         "answer": answer
#     }

@chatRouter.post("/conversations")
def create_new_conversation(db: Session=Depends(get_db)):
    conversation = create_conversation(db)

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
async def chat(message: ChatRequest, db: Session=Depends(get_db)):
    return await process_chat(message.message, message.conversation_id, db)