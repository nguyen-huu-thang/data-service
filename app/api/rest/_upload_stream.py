from collections.abc import AsyncIterator

from fastapi import UploadFile

# Chunk size read from the UploadFile spool on each await. 1 MiB bounds memory
# while keeping the number of awaits low for large files.
# Kích thước chunk đọc từ UploadFile mỗi await - 1 MiB, giữ RAM ổn định.
_CHUNK_SIZE = 1024 * 1024


class UploadFileStream:
    """Adapt a FastAPI UploadFile to the application UploadStream contract.

    Reads the spooled upload in fixed-size chunks so the request body is never
    buffered fully in memory; the use case consumes chunks() once. filename and
    content_type are taken from the UploadFile (with safe fallbacks).
    Bọc UploadFile của FastAPI theo hợp đồng UploadStream của application. Đọc theo
    chunk nên body không buffer hết vào RAM; usecase tiêu thụ chunks() một lần.
    """

    def __init__(self, upload: UploadFile) -> None:
        self.filename = upload.filename or "upload"
        self.content_type = upload.content_type or "application/octet-stream"
        self._upload = upload

    async def chunks(self) -> AsyncIterator[bytes]:
        while True:
            chunk = await self._upload.read(_CHUNK_SIZE)
            if not chunk:
                break
            yield chunk
