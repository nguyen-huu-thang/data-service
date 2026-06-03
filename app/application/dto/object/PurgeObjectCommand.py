from dataclasses import dataclass


@dataclass(frozen=True)
class PurgeObjectCommand:
    requester_identity_id: bytes
    object_id: bytes
