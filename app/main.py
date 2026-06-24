from app.routes.chat_routes import chatRouter
from fastapi import FastAPI
from app.database.connection import engine
from app.database.base import Base

# import schemas
from app.schema.conversation_schema import Conversation
from app.schema.chatmessage_schema import Chatmessage

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(router=chatRouter)