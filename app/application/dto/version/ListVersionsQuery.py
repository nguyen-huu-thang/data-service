from dataclasses import dataclass


@dataclass(frozen=True)
class ListVersionsQuery:
    requester_identity_id: bytes
    object_id: bytes
