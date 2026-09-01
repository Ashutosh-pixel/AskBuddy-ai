import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schema.chatmessage_schema import Chatmessage
from app.schema.conversation_schema import Conversation


async def create_conversation(user_id: uuid.UUID, db: AsyncSession):
    conversation = Conversation(
        user_id= user_id
        # id = str(uuid.uuid4()),
        # title = "New Chat"
    )

    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return conversation

async def get_conversation(db: AsyncSession, conversation_id: uuid.UUID):
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))

    conversation = result.scalars().first()

    if conversation is None:
        return None

    count = await db.execute(select(func.count(Chatmessage.id)).where(Chatmessage.conversation_id == conversation_id))

    message_count = count.scalar_one()

    conversation.message_count = message_count

    return conversation