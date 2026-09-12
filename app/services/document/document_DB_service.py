from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.schema.document_schema import Document


async def save_metadata_db(user_id: UUID, filename: str, stored_filename:str, path:str, size:int, mime_type:str, db: AsyncSession):
    try:
        document = Document(
            original_filename=filename,
            stored_filename=stored_filename,
            file_path=path,
            mime_type=mime_type,
            size=size,
            status="uploaded",
            user_id=user_id
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        return document

    except SQLAlchemyError:
        await db.rollback()
        raise
