from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadObjectQuery:
    requester_identity_id: bytes
    object_id: bytes
