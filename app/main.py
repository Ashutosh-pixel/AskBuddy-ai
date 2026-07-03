from app.models.chat_model import ChatResponse
from app.routes.chat_routes import chatRouter
from fastapi import FastAPI
from app.database.connection import engine
from app.database.base import Base

# import schemas
from app.schema.conversation_schema import Conversation
from app.schema.chatmessage_schema import Chatmessage
from app.services.stream_llm_service import stream_llm

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(router=chatRouter)
