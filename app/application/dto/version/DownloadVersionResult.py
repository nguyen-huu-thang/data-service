from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadVersionResult:
    data: bytes
    mime_type: str
    content_hash: str
    version_number: int
