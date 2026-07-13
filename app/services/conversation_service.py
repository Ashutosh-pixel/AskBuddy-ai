import uuid

from sqlalchemy import func

from app.schema.chatmessage_schema import Chatmessage
from app.schema.conversation_schema import Conversation


def create_conversation(db):
    conversation = Conversation(
        # id = str(uuid.uuid4()),
        # title = "New Chat"
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation

def get_conversation(db, conversation_id: uuid.UUID):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

    message_count = db.query(func.count(Chatmessage.id)).filter(Chatmessage.conversation_id == conversation_id).scalar()

    conversation.message_count = message_count

    return conversation