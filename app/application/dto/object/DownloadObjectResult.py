from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadObjectResult:
    # Resolved blob location and content type after authorization + audit.
    # The blob bytes are NOT read here: the REST adapter streams them lazily and
    # the gRPC adapter loads them, so large objects never buffer in the use case.
    # Vị trí blob và content type đã phân giải sau authz + audit. KHÔNG đọc bytes ở
    # đây: REST stream lười, gRPC tải bytes, nên object lớn không buffer trong usecase.
    storage_pointer: str
    mime_type: str
