from uuid import UUID

from fastapi import APIRouter, Depends, Request, UploadFile
from app.models.query_model import CustomQuery
from app.services.embedding.embedding_service import Embedding
from app.services.tokenize.tokenizer_service import Chunker
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.services.document.document_service import document_service
from app.services.document.parser_service import parser_service
from app.services.vector.vector_service import similarity_search, store_embeddings
from app.services.rag.rag_llm_service import RAG_llm

documentRouter = APIRouter(prefix="/api/documents")

@documentRouter.post("/upload")
async def upload_document(user_id: UUID, file: UploadFile, db:AsyncSession=Depends(get_db)):
    return await document_service(user_id=user_id, file=file,db=db)

@documentRouter.get("/{documentid}")
async def fetch_document(documentid:UUID, db:AsyncSession=Depends(get_db)):
    return await parser_service(documentid,db=db)

@documentRouter.post("/embed")
async def create_embeddings(request: Request, user_id: UUID, text: str, document_id: UUID):
    tokenizer = request.app.state.tokenizer
    embedding_service: Embedding = request.app.state.embedding_service

    # custom chunks
    chunker = Chunker(tokenizer=tokenizer, chunkSize=200, overlap=10)
    chunks = chunker.chunk(text=text)

    # embeddings generate
    embeddings = embedding_service.embed_chunks(chunks=chunks)

    # store embeddings in qdrant
    await store_embeddings(user_id=user_id, document_id=document_id, chunks=chunks, embeddings=embeddings)

    return {
        "message": "Chunks embedded successfully",
        "total_chunks": len(chunks),
        "embedding_count": len(embeddings),
    }

@documentRouter.post("/search/similarity")
async def search(request:Request, data: CustomQuery):
    embedding_service: Embedding = request.app.state.embedding_service

    chunks = []
    chunks.append(data.text)

    # embeddings generate
    embeddings = embedding_service.embed_chunks(chunks=chunks)[0]

    # vector similarity search
    context = await similarity_search(user_id=data.user_id, embedding=embeddings, top_k=data.top_k)

    # LLM service
    result = await RAG_llm(context=context,question=data.text)

    return {
        "message": "Vector search completed",
        "query": data.text,
        "response": result
    }