from dataclasses import dataclass


@dataclass(frozen=True)
class DeleteObjectCommand:
    requester_identity_id: bytes
    object_id: bytes
