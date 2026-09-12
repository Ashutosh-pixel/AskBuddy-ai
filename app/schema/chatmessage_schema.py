from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, Uuid, func, Enum as SQLEnum
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey

from app.database.base import Base

if TYPE_CHECKING:
    from app.schema.conversation_schema import Conversation

class role(Enum):
    SYSTEM="system"
    USER="user"
    ASSISTANT="assistant"
    

class Chatmessage(Base):
    __tablename__ = "chatmessages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    role: Mapped[str] = mapped_column(SQLEnum(role), nullable=False)
    content: Mapped[str] = mapped_column(MEDIUMTEXT)
    conversation_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("conversations.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")