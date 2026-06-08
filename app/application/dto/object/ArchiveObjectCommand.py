from dataclasses import dataclass


@dataclass(frozen=True)
class ArchiveObjectCommand:
    requester_identity_id: bytes
    requester_subject_type: str
    requester_name: str
    object_id: bytes
