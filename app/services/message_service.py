import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.schema.chatmessage_schema import Chatmessage
from app.schema.conversation_schema import Conversation


async def save_message(db: AsyncSession, conversation_id: uuid.UUID, content: str | None, role: str):
    message = Chatmessage(
        conversation_id=conversation_id,
        role=role,
        content=content
    )

    db.add(message)
    await db.commit()
    await db.refresh(message)

    return message

async def get_messages(db: AsyncSession, conversation_id: uuid.UUID):
    result = await db.execute(
        select(Chatmessage)
        .where(Chatmessage.conversation_id == conversation_id)
        .order_by(Chatmessage.created_at)
    )

    return result.scalars().all()