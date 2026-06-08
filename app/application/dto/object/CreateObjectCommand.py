from dataclasses import dataclass

from app.domain.object.valueobject.ObjectType import ObjectType
from app.domain.object.valueobject.ObjectVisibility import ObjectVisibility


@dataclass(frozen=True)
class CreateObjectCommand:
    requester_identity_id: bytes
    requester_subject_type: str
    requester_name: str
    object_type: ObjectType
    visibility: ObjectVisibility
    filename: str
    content_type: str
    data: bytes
    tenant_id: str | None = None
