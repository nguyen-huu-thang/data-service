from dataclasses import dataclass

from app.domain.sharedkernel.model.Id import Id

from app.domain.object.valueobject.ObjectVisibility import ObjectVisibility


@dataclass(frozen=True)
class ChangeObjectVisibilityCommand:
    requester_identity_id: Id
    requester_subject_type: str
    requester_name: str
    object_id: Id
    visibility: ObjectVisibility
