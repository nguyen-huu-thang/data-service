from dataclasses import dataclass


@dataclass(frozen=True)
class RevokeSubjectPermissionCommand:
    requester_identity_id: bytes
    requester_subject_type: str
    requester_name: str
    permission_id: bytes
