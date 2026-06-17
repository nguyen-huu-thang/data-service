from dataclasses import dataclass

from app.domain.sharedkernel.model.Id import Id


@dataclass(frozen=True)
class CreateObjectReferenceResult:
    reference_id: Id
