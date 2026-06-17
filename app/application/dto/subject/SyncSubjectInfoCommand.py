from dataclasses import dataclass

from app.domain.sharedkernel.model.Id import Id


@dataclass(frozen=True)
class SyncSubjectInfoCommand:
    identity_id: Id
    subject_type: str
    name: str
