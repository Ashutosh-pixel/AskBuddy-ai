from uuid import UUID

from fastapi import Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.services.document.document_DB_service import save_metadata_db
from app.services.document.document_S3_service import upload_file


async def document_service(user_id: UUID, file: UploadFile, db:AsyncSession=Depends(get_db)):
    s3_data = await upload_file(file=file)
    return await save_metadata_db(user_id, s3_data["filename"], s3_data["stored_filename"], s3_data["key"], s3_data["size"], s3_data["type"], db)
