from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import VARCHAR, DateTime, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.schema.chatmessage_schema import Chatmessage
    from app.schema.user_schema import User

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(VARCHAR(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    messages: Mapped[list["Chatmessage"]] = relationship(back_populates="conversation")
    user: Mapped["User"] = relationship(back_populates="conversations")