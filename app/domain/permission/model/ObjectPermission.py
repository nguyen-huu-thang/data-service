from datetime import datetime

from app.domain.permission.capability.AclCapability import AclCapability
from app.domain.permission.role.Role import Role

# Role → allowed ACL capabilities
_ROLE_CAPABILITIES: dict[Role, frozenset[AclCapability]] = {
    Role.OWNER: frozenset({
        AclCapability.READ, AclCapability.WRITE, AclCapability.DELETE,
        AclCapability.SHARE, AclCapability.DOWNLOAD,
    }),
    Role.EDITOR: frozenset({
        AclCapability.READ, AclCapability.WRITE, AclCapability.DOWNLOAD,
    }),
    Role.VIEWER: frozenset({
        AclCapability.READ, AclCapability.DOWNLOAD,
    }),
}


class ObjectPermission:

    def __init__(
        self,
        permission_id: bytes,
        object_id: bytes,
        subject_identity_id: bytes,
        subject_type: str,
        role: Role,
        created_at: datetime,
    ) -> None:
        self._permission_id = permission_id

        self._object_id = object_id

        self._subject_identity_id = subject_identity_id
        self._subject_type = subject_type

        self._role = role

        self._created_at = created_at

    @property
    def permission_id(self) -> bytes:
        return self._permission_id

    @property
    def object_id(self) -> bytes:
        return self._object_id

    @property
    def subject_identity_id(self) -> bytes:
        return self._subject_identity_id

    @property
    def subject_type(self) -> str:
        return self._subject_type

    @property
    def role(self) -> Role:
        return self._role

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def has_capability(self, capability: AclCapability) -> bool:
        return capability in _ROLE_CAPABILITIES.get(self._role, frozenset())
