from dataclasses import dataclass

from app.domain.sharedkernel.model.Id import Id


@dataclass(frozen=True)
class CreateVersionCommand:
    requester_identity_id: Id
    requester_subject_type: str
    requester_name: str
    object_id: Id
    filename: str
    content_type: str   # MIME type, e.g. image/jpeg
    data: bytes         # binary content
