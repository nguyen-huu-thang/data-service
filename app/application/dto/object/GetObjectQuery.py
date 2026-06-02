from dataclasses import dataclass


@dataclass(frozen=True)
class GetObjectQuery:
    requester_identity_id: bytes
    object_id: bytes
