"""
Unit tests — DataObject state machine and domain queries.
All tests are synchronous; no DB or external deps.
"""
from datetime import datetime, timezone

import pytest

from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.object.valueobject.ObjectVisibility import ObjectVisibility
from test.conftest import _T0, make_object

_T1 = datetime(2026, 6, 3, tzinfo=timezone.utc)  # later than _T0


# ── Immutable state transitions ───────────────────────────────────────────────

def test_archive_returns_new_instance_with_archived_status():
    obj = make_object(status=ObjectStatus.ACTIVE)
    archived = obj.archive(_T1)
    assert archived.status == ObjectStatus.ARCHIVED
    assert archived is not obj

def test_archive_does_not_mutate_original():
    obj = make_object(status=ObjectStatus.ACTIVE)
    obj.archive(_T1)
    assert obj.status == ObjectStatus.ACTIVE

def test_soft_delete_transitions_to_soft_deleted():
    obj = make_object(status=ObjectStatus.ACTIVE)
    deleted = obj.soft_delete(_T1)
    assert deleted.status == ObjectStatus.SOFT_DELETED
    assert obj.status == ObjectStatus.ACTIVE

def test_restore_transitions_to_active():
    obj = make_object(status=ObjectStatus.SOFT_DELETED)
    restored = obj.restore(_T1)
    assert restored.status == ObjectStatus.ACTIVE
    assert obj.status == ObjectStatus.SOFT_DELETED

def test_restore_from_archived_transitions_to_active():
    obj = make_object(status=ObjectStatus.ARCHIVED)
    restored = obj.restore(_T1)
    assert restored.status == ObjectStatus.ACTIVE

def test_purge_transitions_to_purged():
    obj = make_object(status=ObjectStatus.SOFT_DELETED)
    purged = obj.purge(_T1)
    assert purged.status == ObjectStatus.PURGED
    assert obj.status == ObjectStatus.SOFT_DELETED

def test_state_transition_updates_updated_at():
    obj = make_object()
    assert obj.updated_at == _T0
    archived = obj.archive(_T1)
    assert archived.updated_at == _T1

def test_update_version_sets_current_version_id():
    obj = make_object()
    vid = b'\xBB' * 24
    updated = obj.update_version(vid, _T1)
    assert updated.current_version_id == vid
    assert obj.current_version_id is None  # original unchanged

def test_update_version_updates_updated_at():
    obj = make_object()
    updated = obj.update_version(b'\xBB' * 24, _T1)
    assert updated.updated_at == _T1

def test_increase_permission_version_increments_by_one():
    obj = make_object(permission_version=3)
    updated = obj.increase_permission_version(_T1)
    assert updated.permission_version == 4
    assert obj.permission_version == 3  # original unchanged


# ── State machine — can_transition_to ────────────────────────────────────────

@pytest.mark.parametrize("status,target,expected", [
    # ACTIVE → valid
    (ObjectStatus.ACTIVE, ObjectStatus.ARCHIVED,     True),
    (ObjectStatus.ACTIVE, ObjectStatus.SOFT_DELETED, True),
    # ACTIVE → invalid (must soft-delete before purge)
    (ObjectStatus.ACTIVE, ObjectStatus.PURGED,       False),
    # ARCHIVED → valid
    (ObjectStatus.ARCHIVED, ObjectStatus.ACTIVE,       True),
    (ObjectStatus.ARCHIVED, ObjectStatus.SOFT_DELETED, True),
    # ARCHIVED → invalid (can't jump straight to PURGED)
    (ObjectStatus.ARCHIVED, ObjectStatus.PURGED,       False),
    # SOFT_DELETED → valid
    (ObjectStatus.SOFT_DELETED, ObjectStatus.ACTIVE, True),   # restore
    (ObjectStatus.SOFT_DELETED, ObjectStatus.PURGED, True),
    # SOFT_DELETED → invalid
    (ObjectStatus.SOFT_DELETED, ObjectStatus.ARCHIVED, False),
    # PURGED → terminal, nothing allowed
    (ObjectStatus.PURGED, ObjectStatus.ACTIVE,       False),
    (ObjectStatus.PURGED, ObjectStatus.ARCHIVED,     False),
    (ObjectStatus.PURGED, ObjectStatus.SOFT_DELETED, False),
])
def test_can_transition_to(status, target, expected):
    obj = make_object(status=status)
    assert obj.can_transition_to(target) == expected


# ── Domain queries ────────────────────────────────────────────────────────────

def test_is_deleted_for_soft_deleted_and_purged():
    assert not make_object(status=ObjectStatus.ACTIVE).is_deleted()
    assert not make_object(status=ObjectStatus.ARCHIVED).is_deleted()
    assert make_object(status=ObjectStatus.SOFT_DELETED).is_deleted()
    assert make_object(status=ObjectStatus.PURGED).is_deleted()

def test_is_public_only_for_public_visibility():
    assert make_object(visibility=ObjectVisibility.PUBLIC).is_public()
    assert not make_object(visibility=ObjectVisibility.PRIVATE).is_public()
    assert not make_object(visibility=ObjectVisibility.INTERNAL).is_public()
