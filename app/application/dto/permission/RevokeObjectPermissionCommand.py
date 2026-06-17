from dataclasses import dataclass

from app.domain.sharedkernel.model.Id import Id


@dataclass(frozen=True)
class RevokeObjectPermissionCommand:
    requester_identity_id: Id
    requester_subject_type: str
    requester_name: str
    object_id: Id
    target_identity_id: Id
