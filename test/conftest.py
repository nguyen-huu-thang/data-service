"""
Common test helpers shared across unit and integration tests.
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.domain.object.model.DataObject import DataObject
from app.domain.object.model.ObjectVersion import ObjectVersion
from app.domain.object.valueobject.ContentHash import ContentHash
from app.domain.object.valueobject.MimeType import MimeType
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.object.valueobject.ObjectType import ObjectType
from app.domain.object.valueobject.ObjectVisibility import ObjectVisibility
from app.domain.sharedkernel.model.Id import Id

_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _as_id(value):
    """Coerce a raw bytes test id into an Id value object (None stays None)."""
    if value is None or isinstance(value, Id):
        return value
    return Id(value)

# Fixed IDs — deterministic, easy to reason about in tests
OWNER_ID   = b'\x01' * 24
OTHER_ID   = b'\x02' * 24
OBJECT_ID  = b'\xAA' * 24
VERSION_ID = b'\xBB' * 24
PERM_ID    = b'\xCC' * 24


def make_object(**overrides) -> DataObject:
    """Build a minimal valid DataObject for unit tests."""
    defaults: dict = dict(
        object_id=OBJECT_ID,
        tenant_id=None,
        shard_id="DATA_SHARD_01",
        owner_identity_id=OWNER_ID,
        owner_subject_type="HUMAN",
        object_type=ObjectType("IMAGE"),
        visibility=ObjectVisibility.PRIVATE,
        status=ObjectStatus.ACTIVE,
        current_version_id=None,
        storage_provider="LOCAL",
        storage_pointer="test/path/file.jpg",
        metadata={},
        permission_version=1,
        created_at=_T0,
        updated_at=_T0,
    )
    defaults.update(overrides)
    defaults["object_id"] = _as_id(defaults["object_id"])
    defaults["owner_identity_id"] = _as_id(defaults["owner_identity_id"])
    defaults["current_version_id"] = _as_id(defaults["current_version_id"])
    return DataObject(**defaults)


def make_version(**overrides) -> ObjectVersion:
    """Build a minimal valid ObjectVersion for unit tests."""
    defaults: dict = dict(
        version_id=VERSION_ID,
        object_id=OBJECT_ID,
        version_number=1,
        storage_pointer="test/path/v1.jpg",
        content_hash=ContentHash("ab" * 32),
        content_size=1024,
        mime_type=MimeType("image/jpeg"),
        created_by_identity_id=OWNER_ID,
        created_by_subject_type="HUMAN",
        created_at=_T0,
    )
    defaults.update(overrides)
    defaults["version_id"] = _as_id(defaults["version_id"])
    defaults["object_id"] = _as_id(defaults["object_id"])
    defaults["created_by_identity_id"] = _as_id(defaults["created_by_identity_id"])
    return ObjectVersion(**defaults)


# ── Mock factories ────────────────────────────────────────────────────────────

@asynccontextmanager
async def _noop_tx():
    yield


def mock_tx() -> MagicMock:
    """Callable mock that returns a no-op async context manager on each call."""
    return MagicMock(side_effect=lambda: _noop_tx())


def mock_audit() -> MagicMock:
    """Mock AuditService with an async no-op record() method."""
    svc = MagicMock()
    svc.record = AsyncMock(return_value=None)
    return svc


def mock_auth(*, allow: bool = True) -> MagicMock:
    """Mock AuthorizationService. allow=False raises a permission-denied PublicError."""
    from app.common.exception.AppException import PublicError
    svc = MagicMock()
    if allow:
        svc.require_capability = AsyncMock(return_value=None)
    else:
        svc.require_capability = AsyncMock(side_effect=PublicError("E007004"))
    return svc


def mock_storage(*, blob: bytes = b"") -> MagicMock:
    """Mock the framework StorageService. put/delete are async no-ops; get returns
    `blob`. put_stream DRAINS the async chunk iterator so a BlobWriter built on top
    still computes the real content hash/size. Used by use cases that write/remove
    blobs (create, version, purge).
    Mock StorageService: put/delete no-op async; get trả `blob`; put_stream rút hết
    iterator để BlobWriter tính đúng hash/size."""
    svc = MagicMock()
    svc.put = AsyncMock(return_value=None)
    svc.get = AsyncMock(return_value=blob)
    svc.delete = AsyncMock(return_value=None)
    svc.exists = AsyncMock(return_value=True)

    async def _drain(key, chunks, content_type=None):
        async for _ in chunks:
            pass

    svc.put_stream = AsyncMock(side_effect=_drain)
    return svc


def mock_runtime_config(**values) -> MagicMock:
    """Mock RuntimeConfig.get(key, default) backed by a dict (default-aware)."""
    cfg = MagicMock()
    cfg.get.side_effect = lambda key, default=None: values.get(key, default)
    return cfg
