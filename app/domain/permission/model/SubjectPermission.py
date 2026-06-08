from datetime import datetime

from app.domain.permission.capability.ObjectCapability import (
    ObjectCapability,
)
from app.domain.subject.valueobject.SubjectType import (
    SubjectType,
)


class SubjectPermission:

    def __init__(
        self,
        permission_id: bytes,
        subject_identity_id: bytes,
        subject_type: SubjectType,
        permission: ObjectCapability,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        self._permission_id = permission_id

        self._subject_identity_id = subject_identity_id

        self._subject_type = subject_type

        self._permission = permission

        self._created_at = created_at
        self._updated_at = updated_at

    @property
    def permission_id(self) -> bytes:
        return self._permission_id

    @property
    def subject_identity_id(self) -> bytes:
        return self._subject_identity_id

    @property
    def subject_type(self) -> SubjectType:
        return self._subject_type

    @property
    def permission(self) -> ObjectCapability:
        return self._permission

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def update_permission(
        self,
        permission: ObjectCapability,
        updated_at: datetime,
    ) -> None:
        self._permission = permission
        self._updated_at = updated_at