from dataclasses import dataclass

from app.domain.sharedkernel.model.Id import Id

from app.domain.permission.role.Role import Role


@dataclass(frozen=True)
class GrantObjectPermissionCommand:
    requester_identity_id: Id
    requester_subject_type: str
    requester_name: str
    object_id: Id
    target_identity_id: Id
    target_subject_type: str
    role: Role
