from dataclasses import dataclass


@dataclass(frozen=True)
class CreateVersionCommand:
    requester_identity_id: bytes
    object_id: bytes
    filename: str
    content_type: str   # MIME type, e.g. image/jpeg
    data: bytes         # binary content
