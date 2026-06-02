from dataclasses import dataclass

from app.common.constants.ObjectType import ObjectType
from app.common.constants.Visibility import Visibility


@dataclass(frozen=True)
class CreateObjectCommand:
    requester_identity_id: bytes
    object_type: ObjectType
    visibility: Visibility
    filename: str
    content_type: str
    data: bytes
    tenant_id: str | None = None
