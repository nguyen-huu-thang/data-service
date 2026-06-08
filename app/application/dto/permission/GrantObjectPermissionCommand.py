from dataclasses import dataclass

from app.domain.permission.role.Role import Role


@dataclass(frozen=True)
class GrantObjectPermissionCommand:
    requester_identity_id: bytes
    requester_subject_type: str
    requester_name: str
    object_id: bytes
    target_identity_id: bytes
    target_subject_type: str
    role: Role
