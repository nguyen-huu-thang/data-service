"""
Unit tests — BlobWriter:
  - streams the source into storage, computing the correct SHA-256 + size
  - rejects an upload that exceeds storage.max_upload_bytes with a public 413
  - treats max_upload_bytes == 0 as unlimited
"""
import hashlib

import pytest

from test._app_errors import raises_app

from app.application.dto.upload.UploadStream import BytesUploadStream
from app.application.service.storage.BlobWriter import BlobWriter
from test.conftest import mock_runtime_config, mock_storage

pytestmark = pytest.mark.asyncio


async def test_computes_hash_and_size():
    data = b"hello world payload"
    storage = mock_storage()
    writer = BlobWriter(storage, mock_runtime_config())

    stored = await writer.write("k/obj/file", BytesUploadStream(data, "f", "text/plain"))

    assert stored.content_size == len(data)
    assert stored.content_hash == hashlib.sha256(data).hexdigest()
    storage.put_stream.assert_called_once()


async def test_rejects_when_over_max_bytes():
    data = b"x" * 100
    storage = mock_storage()
    writer = BlobWriter(storage, mock_runtime_config(**{"storage.max_upload_bytes": 10}))

    with raises_app("E067003"):
        await writer.write("k/obj/file", BytesUploadStream(data, "f", "application/octet-stream"))


async def test_unlimited_when_max_bytes_zero():
    data = b"y" * 5000
    storage = mock_storage()
    writer = BlobWriter(storage, mock_runtime_config(**{"storage.max_upload_bytes": 0}))

    stored = await writer.write("k/obj/file", BytesUploadStream(data, "f", "application/octet-stream"))

    assert stored.content_size == 5000
