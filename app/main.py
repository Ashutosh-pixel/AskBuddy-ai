from contextlib import asynccontextmanager


from app.routes.chat_routes import chatRouter
from fastapi import FastAPI
from app.database.connection import engine
from app.database.base import Base

# import schemas
from app.routes.document_routes import documentRouter
from app.services.embedding.embedding_service import Embedding
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        print("Loading BGE-M3 Model & Tokenizer into RAM...")
        BGE_M3_TOKENIZER = AutoTokenizer.from_pretrained("BAAI/bge-m3")
        BGE_M3_MODEL = SentenceTransformer("BAAI/bge-m3")
        BGE_M3_MODEL.eval()

        # app.state (attach model,tokenizer)
        app.state.tokenizer = BGE_M3_TOKENIZER
        app.state.embedding_service = Embedding(model=BGE_M3_MODEL)
        print("Model loaded successfully!")

    yield
    # ==================== SHUTDOWN ====================
    print("Cleaning up resources...")
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.include_router(router=chatRouter)
app.include_router(router=documentRouter)