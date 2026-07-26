from contextlib import asynccontextmanager

from app.models.chat_model import ChatResponse
from app.routes.chat_routes import chatRouter
from fastapi import FastAPI
from app.database.connection import engine
from app.database.base import Base

# import schemas
from app.routes.document_routes import documentRouter
from app.schema.conversation_schema import Conversation
from app.schema.chatmessage_schema import Chatmessage
from app.services.stream_llm_service import stream_llm

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.include_router(router=chatRouter)
app.include_router(router=documentRouter)
