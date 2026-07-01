from uuid import UUID

from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    conversation_id: UUID

class ChatResponse(BaseModel):
    answer: str|None

class MessageCreate(BaseModel):
    content: str
