from dataclasses import dataclass

from app.domain.sharedkernel.model.Id import Id


@dataclass(frozen=True)
class CreateVersionResult:
    version_id: Id
    version_number: int
    content_hash: str
