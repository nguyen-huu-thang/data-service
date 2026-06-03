from dataclasses import dataclass


@dataclass(frozen=True)
class CreateVersionResult:
    version_id: bytes
    version_number: int
    content_hash: str
