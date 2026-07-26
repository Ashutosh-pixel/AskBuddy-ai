import uuid
import asyncio

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, UploadFile

from app.services.document.S3_service import BUCKET, s3

async def upload_file(file:UploadFile):
    return await asyncio.to_thread(_upload_file_sync, file)


def _upload_file_sync(file:UploadFile):
    try:
        extension=file.filename.split(".")[-1]
        stored_filename = f"{uuid.uuid4()}.{extension}"
        key = f"askmybuddy/storage/{stored_filename}"

        s3.upload_fileobj(
            Fileobj=file.file,
            Bucket=BUCKET,
            Key=key,
            ExtraArgs={
                "ContentType": file.content_type
            }
        )

        return{
            "key":key,
            "filename":file.filename,
            "stored_filename":stored_filename,
            "type": file.content_type,
            "size": file.size
        }

    except (ClientError, BotoCoreError) as e:
        raise HTTPException(
            status_code=500,
            detail=f"S3 upload failed: {str(e)}"
        )
