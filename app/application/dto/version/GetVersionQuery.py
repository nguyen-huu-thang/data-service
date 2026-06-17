from dataclasses import dataclass

from app.domain.sharedkernel.model.Id import Id


@dataclass(frozen=True)
class GetVersionQuery:
    requester_identity_id: Id
    requester_subject_type: str
    requester_name: str
    object_id: Id
    version_id: Id
