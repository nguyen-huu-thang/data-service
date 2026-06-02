from dataclasses import dataclass, replace
from datetime import datetime

from app.common.constants.ObjectStatus import ObjectStatus
from app.common.constants.ObjectType import ObjectType
from app.common.constants.Visibility import Visibility


@dataclass(frozen=True)
class DataObject:
    object_id: bytes                # KSUID 24 bytes — immutable
    owner_identity_id: bytes        # KSUID 24 bytes — immutable
    shard_id: str                   # e.g. "DATA_SHARD_01" — immutable
    object_type: ObjectType
    visibility: Visibility
    status: ObjectStatus
    storage_provider: str           # "MINIO" | "S3" | "FILESYSTEM"
    storage_pointer: str            # path/key in blob storage
    metadata_json: dict
    permission_version: int
    created_at: datetime
    updated_at: datetime
    tenant_id: str | None = None
    current_version_id: bytes | None = None

    # State transitions — return new instance, never mutate

    def archive(self, now: datetime) -> "DataObject":
        return replace(self, status=ObjectStatus.ARCHIVED, updated_at=now)

    def soft_delete(self, now: datetime) -> "DataObject":
        return replace(self, status=ObjectStatus.SOFT_DELETED, updated_at=now)

    def restore(self, now: datetime) -> "DataObject":
        return replace(self, status=ObjectStatus.ACTIVE, updated_at=now)

    def set_current_version(self, version_id: bytes, now: datetime) -> "DataObject":
        return replace(self, current_version_id=version_id, updated_at=now)

    def bump_permission_version(self, now: datetime) -> "DataObject":
        return replace(self, permission_version=self.permission_version + 1, updated_at=now)

    # Queries

    def is_accessible(self) -> bool:
        return self.status == ObjectStatus.ACTIVE

    def is_public(self) -> bool:
        return self.visibility == Visibility.PUBLIC

    def is_deleted(self) -> bool:
        return self.status in (ObjectStatus.SOFT_DELETED, ObjectStatus.PURGED)
