"""
Common test helpers shared across unit and integration tests.
"""
from datetime import datetime, timezone

from app.common.constants.ObjectStatus import ObjectStatus
from app.common.constants.ObjectType import ObjectType
from app.common.constants.Visibility import Visibility
from app.domain.object.DataObject import DataObject

_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)

# Fixed IDs — deterministic, easy to reason about in tests
OWNER_ID  = b'\x01' * 24
OTHER_ID  = b'\x02' * 24
OBJECT_ID = b'\xAA' * 24
VERSION_ID = b'\xBB' * 24
PERM_ID   = b'\xCC' * 24


def make_object(**overrides) -> DataObject:
    """Build a minimal valid DataObject for unit tests."""
    defaults: dict = dict(
        object_id=OBJECT_ID,
        owner_identity_id=OWNER_ID,
        shard_id="DATA_SHARD_01",
        object_type=ObjectType.IMAGE,
        visibility=Visibility.PRIVATE,
        status=ObjectStatus.ACTIVE,
        storage_provider="MINIO",
        storage_pointer="test/path/file.jpg",
        metadata_json={},
        permission_version=1,
        created_at=_T0,
        updated_at=_T0,
    )
    defaults.update(overrides)
    return DataObject(**defaults)
