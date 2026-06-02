import asyncio
import io

from minio import Minio
from minio.error import S3Error


class MinioStorageAdapter:
    def __init__(self, client: Minio, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    async def upload(self, pointer: str, data: bytes, content_type: str) -> None:
        await asyncio.to_thread(
            self._client.put_object,
            self._bucket,
            pointer,
            io.BytesIO(data),
            len(data),
            content_type=content_type,
        )

    async def download(self, pointer: str) -> bytes:
        def _read() -> bytes:
            response = self._client.get_object(self._bucket, pointer)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()

        return await asyncio.to_thread(_read)

    async def delete(self, pointer: str) -> None:
        await asyncio.to_thread(self._client.remove_object, self._bucket, pointer)

    async def exists(self, pointer: str) -> bool:
        def _check() -> bool:
            try:
                self._client.stat_object(self._bucket, pointer)
                return True
            except S3Error as e:
                if e.code == "NoSuchKey":
                    return False
                raise

        return await asyncio.to_thread(_check)

    async def generate_pointer(
        self,
        owner_id: bytes,
        object_id: bytes,
        filename: str,
    ) -> str:
        # Deterministic: owner prefix (4 bytes) / full object hex / filename
        # Same input always → same output (idempotent re-upload safe)
        owner_prefix = owner_id.hex()[:8]
        object_hex = object_id.hex()
        return f"{owner_prefix}/{object_hex}/{filename}"

    async def ensure_bucket(self) -> None:
        """Call once at startup to guarantee the bucket exists."""
        def _ensure() -> None:
            if not self._client.bucket_exists(self._bucket):
                self._client.make_bucket(self._bucket)

        await asyncio.to_thread(_ensure)
