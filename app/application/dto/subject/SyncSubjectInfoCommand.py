from dataclasses import dataclass


@dataclass(frozen=True)
class SyncSubjectInfoCommand:
    identity_id: bytes
    subject_type: str
    name: str
