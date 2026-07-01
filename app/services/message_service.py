import uuid

from app.schema.chatmessage_schema import Chatmessage
from app.schema.conversation_schema import Conversation


def save_message(db, conversation_id:uuid.UUID, content:str|None, role:str):
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