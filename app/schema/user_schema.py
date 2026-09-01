from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import VARCHAR, DateTime, Uuid, func

from app.database.base import Base

from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.schema.conversation_schema import Conversation
    from app.schema.document_schema import Document

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(VARCHAR(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(VARCHAR(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user")
    documents: Mapped[list["Document"]] = relationship(back_populates="user")