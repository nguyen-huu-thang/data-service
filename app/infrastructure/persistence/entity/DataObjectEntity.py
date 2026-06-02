from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, JSON, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class DataObjectEntity(Base):
    __tablename__ = "data_object"

    object_id: Mapped[bytes] = mapped_column(LargeBinary(24), primary_key=True)
    owner_identity_id: Mapped[bytes] = mapped_column(LargeBinary(24), nullable=False)
    tenant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shard_id: Mapped[str] = mapped_column(String(30), nullable=False)
    object_type: Mapped[str] = mapped_column(String(20), nullable=False)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    current_version_id: Mapped[bytes | None] = mapped_column(LargeBinary(24), nullable=True)
    storage_provider: Mapped[str] = mapped_column(String(20), nullable=False)
    storage_pointer: Mapped[str] = mapped_column(String(500), nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    permission_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index(
            "ix_data_object_owner_tenant_status_type",
            "owner_identity_id", "tenant_id", "status", "object_type",
        ),
    )
