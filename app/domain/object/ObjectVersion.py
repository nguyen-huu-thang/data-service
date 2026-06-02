from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ObjectVersion:
    version_id: bytes       # KSUID 24 bytes
    object_id: bytes        # KSUID 24 bytes
    version_number: int
    storage_pointer: str
    content_hash: str       # SHA-256 hex digest
    content_size: int       # bytes
    mime_type: str
    created_by: bytes       # identity_id of uploader
    created_at: datetime
