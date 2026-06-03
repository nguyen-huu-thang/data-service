from dataclasses import dataclass


@dataclass(frozen=True)
class RestoreObjectCommand:
    requester_identity_id: bytes
    object_id: bytes
