"""
Common test helpers shared across unit and integration tests.
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

# Domain imports — use bare paths (app/ is in pythonpath via pyproject.toml)
from domain.object.model.DataObject import DataObject
from domain.object.model.ObjectVersion import ObjectVersion
from domain.object.valueobject.ContentHash import ContentHash
from domain.object.valueobject.MimeType import MimeType
from domain.object.valueobject.ObjectStatus import ObjectStatus
from domain.object.valueobject.ObjectType import ObjectType
from domain.object.valueobject.ObjectVisibility import ObjectVisibility

_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)

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
    """Mock AuthorizationService. allow=False raises PermissionDeniedException."""
    from app.common.exception.PermissionDeniedException import PermissionDeniedException
    svc = MagicMock()
    if allow:
        svc.require_capability = AsyncMock(return_value=None)
    else:
        svc.require_capability = AsyncMock(side_effect=PermissionDeniedException())
    return svc
