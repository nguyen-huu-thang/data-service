from dataclasses import dataclass

from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.object.valueobject.ObjectType import ObjectType


@dataclass(frozen=True)
class ListObjectsQuery:
    requester_identity_id: bytes
    requester_subject_type: str
    requester_name: str
    owner_identity_id: bytes
    tenant_id: str | None = None
    object_type: ObjectType | None = None
    status: ObjectStatus | None = None
