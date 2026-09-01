from fastapi.params import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.user_model import Client

from app.schema.user_schema import User


async def create_user(data: Client, db: AsyncSession=Depends(get_db)):
    try:
        user = User(
            email=data.email,
            password=data.password
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    except Exception as e:
        # Rollback the changes if an error occurs
        await db.rollback()
        raise e