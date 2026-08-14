import asyncio
from uuid import UUID

import pymupdf
from fastapi import Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.services.document.parse_metadata_service import parse_metadata_service
from app.services.document.S3_service import BUCKET, s3


async def parser_service(documentid:UUID, db:AsyncSession=Depends(get_db)):
    try:
        key = await parse_metadata_service(document_id=documentid, db=db)
        await asyncio.to_thread(parse_document,key)

        return key;

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="parsing failed"
        )


def parse_document(key:str):
    response = s3.get_object(
        Bucket=BUCKET,
        Key= key
    )

    content = response["Body"].read()
    doc = pymupdf.open(stream=content,filetype="pdf")

    for page in doc:
        text = page.get_text()
        print(f"{text}")

    doc.close()
