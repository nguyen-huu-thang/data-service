"""
Integration tests — LocalDiskStorageAdapter using a temporary directory.

These tests run without any external dependencies.
"""
import pytest
import pytest_asyncio
from pathlib import Path
from unittest.mock import MagicMock

from app.infrastructure.storage.local.LocalDiskStorageAdapter import LocalDiskStorageAdapter

pytestmark = pytest.mark.asyncio


def _make_config(root: str) -> MagicMock:
    config = MagicMock()
    config.get.side_effect = lambda key, default=None: root if key == "storage.local.root" else default
    return config


@pytest_asyncio.fixture
async def adapter(tmp_path: Path) -> LocalDiskStorageAdapter:
    return LocalDiskStorageAdapter(_make_config(str(tmp_path)))


# ── upload / download ─────────────────────────────────────────────────────────

async def test_upload_and_download_roundtrip(adapter: LocalDiskStorageAdapter):
    data    = b"hello local disk integration test"
    pointer = "test/hello.txt"

    await adapter.upload(pointer, data, "text/plain")
    result = await adapter.download(pointer)

    assert result == data


async def test_upload_creates_intermediate_directories(adapter: LocalDiskStorageAdapter):
    data    = b"nested"
    pointer = "a/b/c/d/file.bin"

    await adapter.upload(pointer, data, "application/octet-stream")
    result = await adapter.download(pointer)

    assert result == data


# ── exists ────────────────────────────────────────────────────────────────────

async def test_exists_returns_true_after_upload(adapter: LocalDiskStorageAdapter):
    pointer = "test/exists-check.txt"
    await adapter.upload(pointer, b"data", "text/plain")

    assert await adapter.exists(pointer)


async def test_exists_returns_false_for_missing_object(adapter: LocalDiskStorageAdapter):
    assert not await adapter.exists("test/no-such-object.txt")


# ── delete ────────────────────────────────────────────────────────────────────

async def test_delete_removes_object(adapter: LocalDiskStorageAdapter):
    pointer = "test/to-delete.txt"
    await adapter.upload(pointer, b"temporary", "text/plain")
    await adapter.delete(pointer)

    assert not await adapter.exists(pointer)


async def test_delete_nonexistent_is_noop(adapter: LocalDiskStorageAdapter):
    await adapter.delete("test/nonexistent.txt")


# ── download missing ──────────────────────────────────────────────────────────

async def test_download_missing_raises_file_not_found(adapter: LocalDiskStorageAdapter):
    with pytest.raises(FileNotFoundError):
        await adapter.download("test/missing.txt")


# ── generate_pointer ──────────────────────────────────────────────────────────

async def test_generate_pointer_is_deterministic(adapter: LocalDiskStorageAdapter):
    owner_id  = b'\x01' * 24
    object_id = b'\xAA' * 24
    filename  = "photo.jpg"

    ptr_a = await adapter.generate_pointer(owner_id, object_id, filename)
    ptr_b = await adapter.generate_pointer(owner_id, object_id, filename)

    assert ptr_a == ptr_b


async def test_generate_pointer_includes_owner_and_object(adapter: LocalDiskStorageAdapter):
    owner_id  = b'\x01' * 24
    object_id = b'\xAA' * 24

    ptr = await adapter.generate_pointer(owner_id, object_id, "file.txt")

    assert owner_id.hex()[:8] in ptr
    assert object_id.hex() in ptr
