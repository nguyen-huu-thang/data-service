from sqlalchemy import Index, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from xime.starters.sqlalchemy import Base


class ObjectTagEntity(Base):
    __tablename__ = "object_tag"

    object_id: Mapped[bytes] = mapped_column(
        LargeBinary(24),
        primary_key=True,
    )

    tag: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    __table_args__ = (
        Index(
            "ix_object_tag_tag",
            "tag",
        ),
    )