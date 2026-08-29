from pydantic import BaseModel
from uuid import UUID


class CustomQuery(BaseModel):
    document_id: UUID
    top_k:int
    text:str
