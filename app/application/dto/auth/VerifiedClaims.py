from dataclasses import dataclass, field

from app.domain.sharedkernel.model.Id import Id


@dataclass(frozen=True)
class VerifiedClaims:
    identity_id: Id
    token_version: int
    subject_type: str = "HUMAN"
    name: str = ""
