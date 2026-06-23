from collections.abc import AsyncIterator
from typing import Protocol


class UploadStream(Protocol):
    """Transport-neutral streaming source for an uploaded blob.

    REST wraps a FastAPI UploadFile (true streaming); gRPC and tests wrap an
    in-memory bytes payload. A use case consumes chunks() exactly once, computing
    the content hash and size on the fly (see BlobWriter) so a large upload never
    buffers fully in memory.

    Nguồn stream trung lập với transport cho blob upload. REST bọc UploadFile của
    FastAPI (stream thật); gRPC và test bọc bytes trong RAM. Usecase tiêu thụ
    chunks() đúng một lần, tính hash + size trên đường đi (xem BlobWriter) nên
    upload lớn không buffer hết vào RAM.
    """

    filename: str
    content_type: str

    def chunks(self) -> AsyncIterator[bytes]: ...


class BytesUploadStream:
    """UploadStream over a single in-memory bytes payload.

    Used by the gRPC adapter (its unary contract already holds the whole blob in
    one message) and by tests. Yields the payload as one chunk; an empty payload
    yields nothing.
    UploadStream trên một payload bytes trong RAM. Dùng cho adapter gRPC (hợp đồng
    unary vốn giữ cả blob trong một message) và cho test.
    """

    def __init__(self, data: bytes, filename: str, content_type: str) -> None:
        self.filename = filename
        self.content_type = content_type
        self._data = data

    async def chunks(self) -> AsyncIterator[bytes]:
        if self._data:
            yield self._data
