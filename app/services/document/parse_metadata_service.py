from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schema.document_schema import Document


async def parse_metadata_service(document_id: UUID, db:AsyncSession=Depends(get_db)):
    response = await db.execute(select(Document).where(Document.id == document_id))
    metadata = response.scalar_one()
    return metadata.file_path
