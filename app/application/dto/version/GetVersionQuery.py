from dataclasses import dataclass


@dataclass(frozen=True)
class GetVersionQuery:
    requester_identity_id: bytes
    requester_subject_type: str
    requester_name: str
    object_id: bytes
    version_id: bytes
