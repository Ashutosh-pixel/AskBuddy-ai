from pydantic import BaseModel
from uuid import UUID


class CustomQuery(BaseModel):
    top_k: int
    text: str
    conversation_id: UUID
