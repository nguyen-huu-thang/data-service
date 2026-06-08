from dataclasses import dataclass


@dataclass(frozen=True)
class RevokeObjectPermissionCommand:
    requester_identity_id: bytes
    requester_subject_type: str
    requester_name: str
    object_id: bytes
    target_identity_id: bytes
