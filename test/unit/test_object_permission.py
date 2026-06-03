"""
Unit tests — ObjectPermission.has_capability() by role.
"""
from datetime import datetime, timezone

import pytest

from app.common.constants.Capability import Capability
from app.common.constants.Role import Role
from app.domain.permission.ObjectPermission import ObjectPermission

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
_PERM_ID = b'\xCC' * 24
_OBJ_ID  = b'\xAA' * 24
_SUBJ_ID = b'\x02' * 24


def make_permission(role: Role) -> ObjectPermission:
    return ObjectPermission(
        permission_id=_PERM_ID,
        object_id=_OBJ_ID,
        subject_identity_id=_SUBJ_ID,
        role=role,
        created_at=_NOW,
    )


# ── OWNER — full access ───────────────────────────────────────────────────────

@pytest.mark.parametrize("cap", list(Capability))
def test_owner_has_all_capabilities(cap):
    assert make_permission(Role.OWNER).has_capability(cap)


# ── EDITOR ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("cap", [Capability.READ, Capability.WRITE,
                                  Capability.DOWNLOAD, Capability.COMMENT])
def test_editor_has_allowed_capabilities(cap):
    assert make_permission(Role.EDITOR).has_capability(cap)

@pytest.mark.parametrize("cap", [Capability.DELETE, Capability.SHARE])
def test_editor_lacks_destructive_capabilities(cap):
    assert not make_permission(Role.EDITOR).has_capability(cap)


# ── CONTRIBUTOR ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("cap", [Capability.READ, Capability.WRITE, Capability.COMMENT])
def test_contributor_has_allowed_capabilities(cap):
    assert make_permission(Role.CONTRIBUTOR).has_capability(cap)

@pytest.mark.parametrize("cap", [Capability.DELETE, Capability.SHARE, Capability.DOWNLOAD])
def test_contributor_lacks_privileged_capabilities(cap):
    assert not make_permission(Role.CONTRIBUTOR).has_capability(cap)


# ── VIEWER ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("cap", [Capability.READ, Capability.DOWNLOAD])
def test_viewer_has_allowed_capabilities(cap):
    assert make_permission(Role.VIEWER).has_capability(cap)

@pytest.mark.parametrize("cap", [Capability.WRITE, Capability.DELETE,
                                   Capability.SHARE, Capability.COMMENT])
def test_viewer_lacks_write_capabilities(cap):
    assert not make_permission(Role.VIEWER).has_capability(cap)
