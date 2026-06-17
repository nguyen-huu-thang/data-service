from dataclasses import dataclass
from datetime import datetime

from app.domain.sharedkernel.model.Id import Id


@dataclass(frozen=True)
class CreateObjectShareResult:
    share_id: Id
    share_token: str
    expires_at: datetime | None
