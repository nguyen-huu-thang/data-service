"""
Integration tests — MinioStorageAdapter against a real MinIO instance.

Skipped automatically when MINIO_ENDPOINT env var is not set.

To run locally:
    docker run -d -p 9000:9000 -p 9001:9001 \\
        -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin \\
        quay.io/minio/minio server /data --console-address :9001

    MINIO_ENDPOINT=localhost:9000 pytest test/integration/test_minio_adapter.py -v
"""
import os

import pytest
import pytest_asyncio

from app.infrastructure.storage.minio.MinioStorageAdapter import MinioStorageAdapter
from test.integration.conftest import requires_minio

pytestmark = [pytest.mark.asyncio, requires_minio]


def _make_config(endpoint: str, bucket: str = "test-bucket"):
    cfg = {}
    cfg["storage.minio.endpoint"]   = endpoint
    cfg["storage.minio.access_key"] = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    cfg["storage.minio.secret_key"] = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
    cfg["storage.minio.secure"]     = False
    cfg["storage.minio.bucket"]     = bucket

    from unittest.mock import MagicMock
    config = MagicMock()
    config.get.side_effect = lambda key, default=None: cfg.get(key, default)
    return config


@pytest_asyncio.fixture
async def adapter() -> MinioStorageAdapter:
    endpoint = os.environ["MINIO_ENDPOINT"]
    cfg = _make_config(endpoint, bucket=f"test-{os.getpid()}")
    a = MinioStorageAdapter(cfg)
    await a.ensure_bucket()
    return a


# ── upload / download ─────────────────────────────────────────────────────────

async def test_upload_and_download_roundtrip(adapter: MinioStorageAdapter):
    data    = b"hello minio integration test"
    pointer = "test/hello.txt"

    await adapter.upload(pointer, data, "text/plain")
    result = await adapter.download(pointer)

    assert result == data


async def test_exists_returns_true_after_upload(adapter: MinioStorageAdapter):
    pointer = "test/exists-check.txt"
    await adapter.upload(pointer, b"data", "text/plain")

    assert await adapter.exists(pointer)


async def test_exists_returns_false_for_missing_object(adapter: MinioStorageAdapter):
    assert not await adapter.exists("test/no-such-object.txt")


# ── delete ────────────────────────────────────────────────────────────────────

async def test_delete_removes_object(adapter: MinioStorageAdapter):
    pointer = "test/to-delete.txt"
    await adapter.upload(pointer, b"temporary", "text/plain")
    await adapter.delete(pointer)

    assert not await adapter.exists(pointer)


# ── generate_pointer ──────────────────────────────────────────────────────────

async def test_generate_pointer_is_deterministic(adapter: MinioStorageAdapter):
    owner_id  = b'\x01' * 24
    object_id = b'\xAA' * 24
    filename  = "photo.jpg"

    ptr_a = await adapter.generate_pointer(owner_id, object_id, filename)
    ptr_b = await adapter.generate_pointer(owner_id, object_id, filename)

    assert ptr_a == ptr_b


async def test_generate_pointer_includes_owner_and_object(adapter: MinioStorageAdapter):
    owner_id  = b'\x01' * 24
    object_id = b'\xAA' * 24

    ptr = await adapter.generate_pointer(owner_id, object_id, "file.txt")

    assert owner_id.hex()[:8] in ptr
    assert object_id.hex() in ptr
