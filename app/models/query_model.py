from pydantic import BaseModel
from uuid import UUID


class CustomQuery(BaseModel):
    user_id: UUID
    top_k: int
    text: str
