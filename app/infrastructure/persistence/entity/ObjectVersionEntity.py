from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, LargeBinary, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class ObjectVersionEntity(Base):
    __tablename__ = "object_version"

    version_id: Mapped[bytes] = mapped_column(LargeBinary(24), primary_key=True)
    object_id: Mapped[bytes] = mapped_column(
        LargeBinary(24),
        ForeignKey("data_object.object_id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_pointer: Mapped[str] = mapped_column(String(500), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)     # SHA-256 hex
    content_size: Mapped[int] = mapped_column(BigInteger, nullable=False)     # bytes
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created_by: Mapped[bytes] = mapped_column(LargeBinary(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("object_id", "version_number", name="uq_object_version_number"),
        Index("ix_object_version_object_id", "object_id"),
    )
