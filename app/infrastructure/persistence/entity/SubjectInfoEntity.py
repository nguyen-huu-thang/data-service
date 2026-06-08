from datetime import datetime

from sqlalchemy import DateTime, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from xime.starters.sqlalchemy import Base


class SubjectInfoEntity(Base):
    __tablename__ = "subject_info"

    identity_id: Mapped[bytes] = mapped_column(
        LargeBinary(24),
        primary_key=True,
    )

    subject_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )