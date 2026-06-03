from datetime import datetime

from sqlalchemy import DateTime, Index, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from xime.starters.sqlalchemy import Base


class ObjectAuditEntity(Base):
    __tablename__ = "object_audit"

    # No FK to data_object — audit records outlive objects (compliance)
    audit_id: Mapped[bytes] = mapped_column(LargeBinary(24), primary_key=True)
    object_id: Mapped[bytes] = mapped_column(LargeBinary(24), nullable=False)
    actor_identity_id: Mapped[bytes] = mapped_column(LargeBinary(24), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_object_audit_object_id", "object_id"),
        Index("ix_object_audit_actor", "actor_identity_id"),
    )
