from datetime import datetime

from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.object.valueobject.ObjectType import ObjectType
from app.domain.object.valueobject.ObjectVisibility import ObjectVisibility

# Valid state transitions: source -> allowed targets
_ALLOWED_TRANSITIONS: dict[ObjectStatus, frozenset[ObjectStatus]] = {
    ObjectStatus.ACTIVE: frozenset({ObjectStatus.ARCHIVED, ObjectStatus.SOFT_DELETED}),
    ObjectStatus.ARCHIVED: frozenset({ObjectStatus.ACTIVE, ObjectStatus.SOFT_DELETED}),
    ObjectStatus.SOFT_DELETED: frozenset({ObjectStatus.ACTIVE, ObjectStatus.PURGED}),
    ObjectStatus.PURGED: frozenset(),
}


class DataObject:

    def __init__(
        self,
        object_id: bytes,
        tenant_id: str | None,
        shard_id: str,
        owner_identity_id: bytes,
        owner_subject_type: str,
        object_type: ObjectType,
        visibility: ObjectVisibility,
        status: ObjectStatus,
        current_version_id: bytes | None,
        storage_provider: str,
        storage_pointer: str,
        metadata: dict | None,
        permission_version: int,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        self._object_id = object_id
        self._tenant_id = tenant_id
        self._shard_id = shard_id

        self._owner_identity_id = owner_identity_id
        self._owner_subject_type = owner_subject_type

        self._object_type = object_type
        self._visibility = visibility
        self._status = status

        self._current_version_id = current_version_id

        self._storage_provider = storage_provider
        self._storage_pointer = storage_pointer

        self._metadata = metadata or {}

        self._permission_version = permission_version

        self._created_at = created_at
        self._updated_at = updated_at

    # =========================
    # Properties
    # =========================

    @property
    def object_id(self) -> bytes:
        return self._object_id

    @property
    def tenant_id(self) -> str | None:
        return self._tenant_id

    @property
    def shard_id(self) -> str:
        return self._shard_id

    @property
    def owner_identity_id(self) -> bytes:
        return self._owner_identity_id

    @property
    def owner_subject_type(self) -> str:
        return self._owner_subject_type

    @property
    def object_type(self) -> ObjectType:
        return self._object_type

    @property
    def visibility(self) -> ObjectVisibility:
        return self._visibility

    @property
    def status(self) -> ObjectStatus:
        return self._status

    @property
    def current_version_id(self) -> bytes | None:
        return self._current_version_id

    @property
    def storage_provider(self) -> str:
        return self._storage_provider

    @property
    def storage_pointer(self) -> str:
        return self._storage_pointer

    @property
    def metadata(self) -> dict:
        return self._metadata

    @property
    def permission_version(self) -> int:
        return self._permission_version

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    # =========================
    # Query Methods
    # =========================

    def is_public(self) -> bool:
        return self._visibility == ObjectVisibility.PUBLIC

    def is_deleted(self) -> bool:
        return self._status in (ObjectStatus.SOFT_DELETED, ObjectStatus.PURGED)

    def can_transition_to(self, target: ObjectStatus) -> bool:
        return target in _ALLOWED_TRANSITIONS.get(self._status, frozenset())

    # =========================
    # State-change Methods — each returns a new DataObject
    # =========================

    def archive(self, now: datetime) -> 'DataObject':
        return self._copy(status=ObjectStatus.ARCHIVED, updated_at=now)

    def restore(self, now: datetime) -> 'DataObject':
        return self._copy(status=ObjectStatus.ACTIVE, updated_at=now)

    def soft_delete(self, now: datetime) -> 'DataObject':
        return self._copy(status=ObjectStatus.SOFT_DELETED, updated_at=now)

    def purge(self, now: datetime) -> 'DataObject':
        return self._copy(status=ObjectStatus.PURGED, updated_at=now)

    def update_current_version(self, version_id: bytes, now: datetime) -> 'DataObject':
        return self._copy(current_version_id=version_id, updated_at=now)

    def update_version(self, version_id: bytes, now: datetime) -> 'DataObject':
        return self.update_current_version(version_id, now)

    def change_visibility(self, visibility: ObjectVisibility, now: datetime) -> 'DataObject':
        return self._copy(visibility=visibility, updated_at=now)

    def increase_permission_version(self, now: datetime) -> 'DataObject':
        return self._copy(permission_version=self._permission_version + 1, updated_at=now)

    # =========================
    # Internal helpers
    # =========================

    def _copy(self, **overrides) -> 'DataObject':
        return DataObject(
            object_id=overrides.get('object_id', self._object_id),
            tenant_id=overrides.get('tenant_id', self._tenant_id),
            shard_id=overrides.get('shard_id', self._shard_id),
            owner_identity_id=overrides.get('owner_identity_id', self._owner_identity_id),
            owner_subject_type=overrides.get('owner_subject_type', self._owner_subject_type),
            object_type=overrides.get('object_type', self._object_type),
            visibility=overrides.get('visibility', self._visibility),
            status=overrides.get('status', self._status),
            current_version_id=overrides.get('current_version_id', self._current_version_id),
            storage_provider=overrides.get('storage_provider', self._storage_provider),
            storage_pointer=overrides.get('storage_pointer', self._storage_pointer),
            metadata=overrides.get('metadata', self._metadata),
            permission_version=overrides.get('permission_version', self._permission_version),
            created_at=overrides.get('created_at', self._created_at),
            updated_at=overrides.get('updated_at', self._updated_at),
        )
