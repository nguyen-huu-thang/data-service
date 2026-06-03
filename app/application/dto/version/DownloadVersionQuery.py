from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadVersionQuery:
    requester_identity_id: bytes
    object_id: bytes
    version_id: bytes
