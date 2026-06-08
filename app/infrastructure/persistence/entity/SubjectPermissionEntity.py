from datetime import datetime

from sqlalchemy import DateTime, Index, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from xime.starters.sqlalchemy import Base


class SubjectPermissionEntity(Base):
    __tablename__ = "subject_permission"

    permission_id: Mapped[bytes] = mapped_column(
        LargeBinary(24),
        primary_key=True,
    )

    subject_identity_id: Mapped[bytes] = mapped_column(
        LargeBinary(24),
        nullable=False,
    )

    subject_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    permission: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_subject_permission_subject",
            "subject_identity_id",
        ),
        Index(
            "ix_subject_permission_permission",
            "permission",
        ),
    )