from contextlib import asynccontextmanager

from transformers import AutoTokenizer

from app.routes.chat_routes import chatRouter
from fastapi import FastAPI
from app.database.connection import engine
from app.database.base import Base

# import schemas
from app.routes.document_routes import documentRouter
from app.services.tokenize.tokenizer_service import Chunker

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.include_router(router=chatRouter)
app.include_router(router=documentRouter)

tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-m3")
chunker = Chunker(tokenizer=tokenizer,chunkSize=200, overlap=10)
chunker.chunk()