from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadObjectResult:
    data: bytes
    mime_type: str
    content_size: int
