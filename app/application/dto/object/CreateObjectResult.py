from dataclasses import dataclass

from app.domain.sharedkernel.model.Id import Id


@dataclass(frozen=True)
class CreateObjectResult:
    object_id: Id
    shard_id: str
    storage_pointer: str
