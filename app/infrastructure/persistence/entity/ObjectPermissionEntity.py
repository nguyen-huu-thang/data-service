from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    LargeBinary,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from xime.starters.sqlalchemy import Base


class ObjectPermissionEntity(Base):
    __tablename__ = "object_permission"

    permission_id: Mapped[bytes] = mapped_column(
        LargeBinary(24),
        primary_key=True,
    )

    object_id: Mapped[bytes] = mapped_column(
        LargeBinary(24),
        ForeignKey("data_object.object_id", ondelete="CASCADE"),
        nullable=False,
    )

    subject_identity_id: Mapped[bytes] = mapped_column(
        LargeBinary(24),
        nullable=False,
    )

    subject_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "subject_identity_id",
            "object_id",
            name="uq_object_permission_subject_object",
        ),
        Index(
            "ix_object_permission_subject",
            "subject_identity_id",
        ),
        Index(
            "ix_object_permission_object",
            "object_id",
        ),
        Index(
            "ix_object_permission_subject_object",
            "subject_identity_id",
            "object_id",
        ),
    )