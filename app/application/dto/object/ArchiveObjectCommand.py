from dataclasses import dataclass


@dataclass(frozen=True)
class ArchiveObjectCommand:
    requester_identity_id: bytes
    object_id: bytes
