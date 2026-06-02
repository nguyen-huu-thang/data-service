from typing import Protocol


class BlobStoragePort(Protocol):
    async def upload(
        self,
        pointer: str,
        data: bytes,
        content_type: str,
    ) -> None: ...

    async def download(self, pointer: str) -> bytes: ...

    async def delete(self, pointer: str) -> None: ...

    async def exists(self, pointer: str) -> bool: ...

    async def generate_pointer(
        self,
        owner_id: bytes,
        object_id: bytes,
        filename: str,
    ) -> str: ...
