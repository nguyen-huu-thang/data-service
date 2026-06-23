from dataclasses import dataclass


@dataclass(frozen=True)
class StoredBlob:
    # Result of streaming a blob into storage (see BlobWriter).
    # Lives under dto/ (excluded from DI scan) so the scanner never tries to
    # construct it as a component.
    # Kết quả stream blob vào storage (xem BlobWriter). Đặt ở dto/ (loại khỏi DI
    # scan) để scanner không cố dựng nó như component.
    content_hash: str   # SHA-256 hex of the full content
    content_size: int   # total bytes written
