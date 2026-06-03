"""
Unit tests — AuthorizationService: owner bypass, PUBLIC bypass, ACL evaluation.
Ports are mocked; no DB needed.
"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.constants.Capability import Capability
from app.common.constants.Role import Role
from app.common.constants.Visibility import Visibility
from app.common.exception.PermissionDeniedException import PermissionDeniedException
from app.domain.permission.ObjectPermission import ObjectPermission
from test.conftest import OBJECT_ID, OTHER_ID, OWNER_ID, PERM_ID, make_object

pytestmark = pytest.mark.asyncio

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _make_auth(permission: ObjectPermission | None) -> AuthorizationService:
    port = AsyncMock()
    port.find_by_subject_and_object = AsyncMock(return_value=permission)
    return AuthorizationService(load_permission_port=port)


def _make_permission(role: Role) -> ObjectPermission:
    return ObjectPermission(
        permission_id=PERM_ID,
        object_id=OBJECT_ID,
        subject_identity_id=OTHER_ID,
        role=role,
        created_at=_NOW,
    )


# ── Owner bypass ──────────────────────────────────────────────────────────────

async def test_owner_is_allowed_all_capabilities():
    auth = _make_auth(None)
    obj = make_object(owner_identity_id=OWNER_ID)
    for cap in Capability:
        await auth.require_capability(OWNER_ID, obj, cap)  # must not raise


# ── PUBLIC object bypass ──────────────────────────────────────────────────────

async def test_public_object_allows_read_without_acl():
    auth = _make_auth(None)
    obj = make_object(visibility=Visibility.PUBLIC)
    await auth.require_capability(OTHER_ID, obj, Capability.READ)

async def test_public_object_allows_download_without_acl():
    auth = _make_auth(None)
    obj = make_object(visibility=Visibility.PUBLIC)
    await auth.require_capability(OTHER_ID, obj, Capability.DOWNLOAD)

async def test_public_object_still_requires_acl_for_write():
    auth = _make_auth(None)  # no ACL entry
    obj = make_object(visibility=Visibility.PUBLIC)
    with pytest.raises(PermissionDeniedException):
        await auth.require_capability(OTHER_ID, obj, Capability.WRITE)


# ── ACL evaluation ────────────────────────────────────────────────────────────

async def test_viewer_can_read_private_object():
    auth = _make_auth(_make_permission(Role.VIEWER))
    obj = make_object(visibility=Visibility.PRIVATE)
    await auth.require_capability(OTHER_ID, obj, Capability.READ)

async def test_viewer_cannot_write():
    auth = _make_auth(_make_permission(Role.VIEWER))
    obj = make_object(visibility=Visibility.PRIVATE)
    with pytest.raises(PermissionDeniedException):
        await auth.require_capability(OTHER_ID, obj, Capability.WRITE)

async def test_editor_can_write():
    auth = _make_auth(_make_permission(Role.EDITOR))
    obj = make_object()
    await auth.require_capability(OTHER_ID, obj, Capability.WRITE)

async def test_editor_cannot_delete():
    auth = _make_auth(_make_permission(Role.EDITOR))
    obj = make_object()
    with pytest.raises(PermissionDeniedException):
        await auth.require_capability(OTHER_ID, obj, Capability.DELETE)

async def test_no_acl_entry_denies_all_for_private_object():
    auth = _make_auth(None)
    obj = make_object(visibility=Visibility.PRIVATE)
    for cap in Capability:
        with pytest.raises(PermissionDeniedException):
            await auth.require_capability(OTHER_ID, obj, cap)
