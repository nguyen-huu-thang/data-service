from datetime import datetime

from sqlalchemy import Index, DateTime, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from xime.starters.sqlalchemy import Base


class ObjectReferenceEntity(Base):
    __tablename__ = "object_reference"

    reference_id: Mapped[bytes] = mapped_column(
        LargeBinary(24),
        primary_key=True,
    )

    object_id: Mapped[bytes] = mapped_column(
        LargeBinary(24),
        nullable=False,
    )

    application_identity_id: Mapped[bytes] = mapped_column(
        LargeBinary(24),
        nullable=False,
    )

    application_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    resource_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_object_reference_application",
            "application_identity_id",
        ),
        Index(
            "ix_object_reference_object",
            "object_id",
        ),
    )