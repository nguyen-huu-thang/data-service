from datetime import datetime

from sqlalchemy import DateTime, Index, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from xime.starters.sqlalchemy import Base


class ObjectShareEntity(Base):
    __tablename__ = "object_share"

    share_id: Mapped[bytes] = mapped_column(
        LargeBinary(24),
        primary_key=True,
    )

    object_id: Mapped[bytes] = mapped_column(
        LargeBinary(24),
        nullable=False,
    )

    share_token: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_object_share_object",
            "object_id",
        ),
    )