import asyncio
import os
from pathlib import Path

from xime.core.config.runtime import RuntimeConfig


class LocalDiskStorageAdapter:
    def __init__(self, config: RuntimeConfig) -> None:
        root: str = config.get("storage.local.root", "storage")
        self._root = Path(root)

    async def upload(self, pointer: str, data: bytes, content_type: str) -> None:
        path = self._root / pointer

        def _write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        await asyncio.to_thread(_write)

    async def download(self, pointer: str) -> bytes:
        path = self._root / pointer

        def _read() -> bytes:
            if not path.exists():
                raise FileNotFoundError(f"Blob not found: {pointer}")
            return path.read_bytes()

        return await asyncio.to_thread(_read)

    async def delete(self, pointer: str) -> None:
        path = self._root / pointer

        def _delete() -> None:
            if path.exists():
                os.remove(path)

        await asyncio.to_thread(_delete)

    async def exists(self, pointer: str) -> bool:
        return await asyncio.to_thread((self._root / pointer).exists)

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

        # Sanitize filename to prevent path traversal.
        # A malicious filename like "../../other_owner/obj/x" could otherwise
        # escape the {owner}/{object} directory and overwrite another owner's
        # blob. Strip every directory component and keep only the base name.
        safe_name = filename.replace("\\", "/").split("/")[-1]
        if not safe_name or safe_name in (".", ".."):
            safe_name = "upload"

        return f"{owner_prefix}/{object_hex}/{safe_name}"
