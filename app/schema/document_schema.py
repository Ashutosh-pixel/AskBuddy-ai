from typing import TYPE_CHECKING
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import INTEGER, TEXT, VARCHAR, DateTime, ForeignKey, Uuid, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.schema.user_schema import User


class status(Enum):
    UPLOADED="uploaded"
    PROCESSING="processing"
    READY="ready"
    FAILED="failed"

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    original_filename: Mapped[str] = mapped_column(VARCHAR(100))
    stored_filename: Mapped[str] = mapped_column(VARCHAR(100))
    file_path: Mapped[str] = mapped_column(TEXT)
    mime_type: Mapped[str] = mapped_column(VARCHAR(100))
    size: Mapped[int] = mapped_column(INTEGER)
    status: Mapped[str] = mapped_column(SQLEnum(status), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    user:Mapped["User"] = relationship(back_populates="documents")
