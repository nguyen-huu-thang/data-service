from dataclasses import dataclass

from app.domain.permission.capability.ObjectCapability import ObjectCapability


@dataclass(frozen=True)
class GrantSubjectPermissionCommand:
    requester_identity_id: bytes
    requester_subject_type: str
    requester_name: str
    target_identity_id: bytes
    target_subject_type: str
    capability: ObjectCapability
