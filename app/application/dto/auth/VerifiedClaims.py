from dataclasses import dataclass


@dataclass(frozen=True)
class VerifiedClaims:
    identity_id: bytes
    token_version: int
