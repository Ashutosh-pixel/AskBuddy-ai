from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile
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
