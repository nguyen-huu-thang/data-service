"""
Unit tests — ObjectPermission.has_capability() by role.
"""
from datetime import datetime, timezone

import pytest

from domain.permission.capability.AclCapability import AclCapability
from domain.permission.model.ObjectPermission import ObjectPermission
from domain.permission.role.Role import Role

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
_PERM_ID = b'\xCC' * 24
_OBJ_ID  = b'\xAA' * 24
_SUBJ_ID = b'\x02' * 24


def make_permission(role: Role) -> ObjectPermission:
    return ObjectPermission(
        permission_id=_PERM_ID,
        object_id=_OBJ_ID,
        subject_identity_id=_SUBJ_ID,
        subject_type="HUMAN",
        role=role,
        created_at=_NOW,
    )


# ── OWNER — full access ───────────────────────────────────────────────────────

@pytest.mark.parametrize("cap", list(AclCapability))
def test_owner_has_all_capabilities(cap):
    assert make_permission(Role.OWNER).has_capability(cap)


# ── EDITOR ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("cap", [AclCapability.READ, AclCapability.WRITE, AclCapability.DOWNLOAD])
def test_editor_has_allowed_capabilities(cap):
    assert make_permission(Role.EDITOR).has_capability(cap)

@pytest.mark.parametrize("cap", [AclCapability.DELETE, AclCapability.SHARE])
def test_editor_lacks_destructive_capabilities(cap):
    assert not make_permission(Role.EDITOR).has_capability(cap)


# ── VIEWER ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("cap", [AclCapability.READ, AclCapability.DOWNLOAD])
def test_viewer_has_allowed_capabilities(cap):
    assert make_permission(Role.VIEWER).has_capability(cap)

@pytest.mark.parametrize("cap", [AclCapability.WRITE, AclCapability.DELETE, AclCapability.SHARE])
def test_viewer_lacks_write_capabilities(cap):
    assert not make_permission(Role.VIEWER).has_capability(cap)
