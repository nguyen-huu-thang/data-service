from dataclasses import dataclass

from app.domain.sharedkernel.model.Id import Id


@dataclass(frozen=True)
class CreateObjectReferenceCommand:
    requester_identity_id: Id
    requester_subject_type: str
    requester_name: str
    object_id: Id
    application_identity_id: Id
    application_name: str
    resource_type: str
    resource_id: str
