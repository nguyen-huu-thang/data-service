from datetime import datetime

from sqlalchemy import DateTime, Index, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from xime.starters.sqlalchemy import Base


class ObjectAuditEntity(Base):
    __tablename__ = "object_audit"

    audit_id: Mapped[bytes] = mapped_column(
        LargeBinary(24),
        primary_key=True,
    )

    # Nullable: subject-level actions (grant/revoke subject permission, sync)
    # are not tied to any object.
    # Cho phép null: hành động cấp-subject không gắn object nào.
    object_id: Mapped[bytes | None] = mapped_column(
        LargeBinary(24),
        nullable=True,
    )

    actor_identity_id: Mapped[bytes] = mapped_column(
        LargeBinary(24),
        nullable=False,
    )

    actor_subject_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    actor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    action: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_object_audit_object",
            "object_id",
        ),
        Index(
            "ix_object_audit_actor",
            "actor_identity_id",
        ),
    )