from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.user_model import Client
from app.services.user.user_service import create_user


userRouter = APIRouter(prefix="/api")


@userRouter.post("/user")
async def add_new_user(data:Client, db: AsyncSession=Depends(get_db)):
    response = await create_user(data=data,db=db)

    return {
        "message": "User created successfully",
        "id": f"{response.id}"
    }
