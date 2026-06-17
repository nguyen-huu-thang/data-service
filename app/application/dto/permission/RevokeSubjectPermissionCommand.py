from dataclasses import dataclass

from app.domain.sharedkernel.model.Id import Id


@dataclass(frozen=True)
class RevokeSubjectPermissionCommand:
    requester_identity_id: Id
    requester_subject_type: str
    requester_name: str
    permission_id: Id
