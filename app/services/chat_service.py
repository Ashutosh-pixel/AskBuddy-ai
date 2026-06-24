import uuid

from app.schema.chatmessage_schema import Chatmessage
from app.schema.conversation_schema import Conversation


def create_conversation(db):
    conversation = Conversation(
        # id = str(uuid.uuid4()),
        title = "New Chat"
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation

def save_message(db, conversation_id:uuid.UUID, content:str, role:str):
    message = Chatmessage(
        conversation_id=conversation_id,
        role=role,
        content=content
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message

def get_messages(db, conversation_id: uuid.UUID):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

    return conversation.messages