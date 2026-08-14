from uuid import UUID

from fastapi import APIRouter, Depends, Request, UploadFile
from app.services.embedding.embedding_service import Embedding
from app.services.tokenize.tokenizer_service import Chunker
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.services.document.document_service import document_service
from app.services.document.parser_service import parser_service

documentRouter = APIRouter(prefix="/api/documents")

@documentRouter.post("/upload")
async def upload_document(file: UploadFile, db:AsyncSession=Depends(get_db)):
    return document_service(file=file,db=db)

@documentRouter.get("/{documentid}")
async def fetch_document(documentid:UUID, db:AsyncSession=Depends(get_db)):
    return await parser_service(documentid,db=db)

@documentRouter.post("/embed")
async def create_embeddings(request: Request, text: str):
    tokenizer = request.app.state.tokenizer
    embedding_service: Embedding = request.app.state.embedding_service

    # custom chunks
    chunker = Chunker(tokenizer=tokenizer, chunkSize=200, overlap=10)
    chunks = chunker.chunk(text=text)

    # embeddings generate
    embeddings = embedding_service.embed_chunks(chunks=chunks)

    return {
        "message": "Chunks embedded successfully",
        "total_chunks": len(chunks),
        "embedding_count": len(embeddings),
    }