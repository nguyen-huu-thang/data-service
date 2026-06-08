from dataclasses import dataclass, field


@dataclass(frozen=True)
class VerifiedClaims:
    identity_id: bytes
    token_version: int
    subject_type: str = "HUMAN"
    name: str = ""
