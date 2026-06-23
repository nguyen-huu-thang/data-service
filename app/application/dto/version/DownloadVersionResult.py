from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadVersionResult:
    # Resolved blob location + metadata after authorization + audit. The blob
    # bytes are NOT read here (see DownloadObjectResult): the REST adapter streams
    # them lazily and the gRPC adapter loads them.
    # Vị trí blob + metadata đã phân giải sau authz + audit. KHÔNG đọc bytes ở đây.
    storage_pointer: str
    mime_type: str
    content_hash: str
    version_number: int
