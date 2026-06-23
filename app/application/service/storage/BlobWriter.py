import hashlib
from collections.abc import AsyncIterator

from xime.core.config.runtime import RuntimeConfig
from xime.starters.storage import StorageService

from app.application.dto.storage.StoredBlob import StoredBlob
from app.application.dto.upload.UploadStream import UploadStream
from app.common.exception.AppException import PublicError


class BlobWriter:
    """Stream an UploadStream into storage while computing its content hash and
    size, and enforce an optional maximum upload size.

    The blob is written through StorageService.put_stream so it is never buffered
    fully in memory; the hash and size are computed incrementally as chunks pass
    through. When `storage.max_upload_bytes` is configured (> 0) and the running
    total exceeds it, the upload is rejected with a public 413 BEFORE the whole
    body is consumed, and the storage backend cleans up the partial write.

    Stream UploadStream vào storage đồng thời tính hash + size, ép giới hạn kích
    thước tùy chọn. Blob đi qua StorageService.put_stream nên không buffer hết vào
    RAM; hash/size tính dần theo chunk. Vượt `storage.max_upload_bytes` -> 413
    trước khi đọc hết body; backend tự dọn phần ghi dở.
    """

    def __init__(self, storage: StorageService, config: RuntimeConfig) -> None:
        self._storage = storage
        # 0 / unset = no limit. Một số 0 hoặc thiếu cấu hình = không giới hạn.
        self._max_bytes: int = int(config.get("storage.max_upload_bytes", 0) or 0)

    async def write(self, key: str, source: UploadStream) -> StoredBlob:
        hasher = hashlib.sha256()
        size = 0

        async def _hashed() -> AsyncIterator[bytes]:
            nonlocal size
            async for chunk in source.chunks():
                size += len(chunk)
                if self._max_bytes and size > self._max_bytes:
                    # Reject before reading the rest of the body; put_stream's
                    # except-clause removes the partial .part file.
                    # Từ chối trước khi đọc nốt body; put_stream xóa file .part dở.
                    raise PublicError("E067003")
                hasher.update(chunk)
                yield chunk

        await self._storage.put_stream(key, _hashed(), content_type=source.content_type)
        return StoredBlob(content_hash=hasher.hexdigest(), content_size=size)
