from dataclasses import dataclass
from datetime import datetime

from app.domain.sharedkernel.model.Id import Id


@dataclass(frozen=True)
class CreateObjectShareCommand:
    requester_identity_id: Id
    requester_subject_type: str
    requester_name: str
    object_id: Id
    expires_at: datetime | None = None
