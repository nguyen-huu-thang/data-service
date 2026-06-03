from dataclasses import dataclass


@dataclass(frozen=True)
class GetVersionQuery:
    requester_identity_id: bytes
    object_id: bytes
    version_id: bytes
