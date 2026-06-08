from dataclasses import dataclass

from app.domain.object.valueobject.ObjectVisibility import ObjectVisibility


@dataclass(frozen=True)
class ChangeObjectVisibilityCommand:
    requester_identity_id: bytes
    requester_subject_type: str
    requester_name: str
    object_id: bytes
    visibility: ObjectVisibility
