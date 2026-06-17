"""
Unit tests — AuthorizationService: owner bypass, PUBLIC bypass, ACL evaluation.
Ports are mocked; no DB needed.
"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from test._app_errors import raises_app

from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.domain.object.valueobject.ObjectVisibility import ObjectVisibility
from app.domain.permission.capability.AclCapability import AclCapability
from app.domain.permission.model.ObjectPermission import ObjectPermission
from app.domain.permission.policy.AccessPolicy import AccessPolicy
from app.domain.permission.role.Role import Role
from app.domain.sharedkernel.model.Id import Id
from test.conftest import OBJECT_ID, OTHER_ID, OWNER_ID, PERM_ID, make_object

pytestmark = pytest.mark.asyncio

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _make_auth(permission: ObjectPermission | None) -> AuthorizationService:
    port = AsyncMock()
    port.find_by_subject_and_object = AsyncMock(return_value=permission)
    load_subj = AsyncMock()
    load_subj.find_by_subject = AsyncMock(return_value=[])
    return AuthorizationService(
        load_permission_port=port,
        load_subject_permission_port=load_subj,
        access_policy=AccessPolicy(),
    )


def _make_permission(role: Role) -> ObjectPermission:
    return ObjectPermission(
        permission_id=PERM_ID,
        object_id=OBJECT_ID,
        subject_identity_id=OTHER_ID,
        subject_type="HUMAN",
        role=role,
        created_at=_NOW,
    )


# ── Owner bypass ──────────────────────────────────────────────────────────────

async def test_owner_is_allowed_all_capabilities():
    auth = _make_auth(None)
    obj = make_object(owner_identity_id=OWNER_ID)
    for cap in AclCapability:
        await auth.require_capability(Id(OWNER_ID), obj, cap)  # must not raise


# ── PUBLIC object bypass ──────────────────────────────────────────────────────

async def test_public_object_allows_read_without_acl():
    auth = _make_auth(None)
    obj = make_object(visibility=ObjectVisibility.PUBLIC)
    await auth.require_capability(Id(OTHER_ID), obj, AclCapability.READ)

async def test_public_object_allows_download_without_acl():
    auth = _make_auth(None)
    obj = make_object(visibility=ObjectVisibility.PUBLIC)
    await auth.require_capability(Id(OTHER_ID), obj, AclCapability.DOWNLOAD)

async def test_public_object_still_requires_acl_for_write():
    auth = _make_auth(None)  # no ACL entry
    obj = make_object(visibility=ObjectVisibility.PUBLIC)
    with raises_app("E007004"):
        await auth.require_capability(Id(OTHER_ID), obj, AclCapability.WRITE)


# ── ACL evaluation ────────────────────────────────────────────────────────────

async def test_viewer_can_read_private_object():
    auth = _make_auth(_make_permission(Role.VIEWER))
    obj = make_object(visibility=ObjectVisibility.PRIVATE)
    await auth.require_capability(Id(OTHER_ID), obj, AclCapability.READ)

async def test_viewer_cannot_write():
    auth = _make_auth(_make_permission(Role.VIEWER))
    obj = make_object(visibility=ObjectVisibility.PRIVATE)
    with raises_app("E007004"):
        await auth.require_capability(Id(OTHER_ID), obj, AclCapability.WRITE)

async def test_editor_can_write():
    auth = _make_auth(_make_permission(Role.EDITOR))
    obj = make_object()
    await auth.require_capability(Id(OTHER_ID), obj, AclCapability.WRITE)

async def test_editor_cannot_delete():
    auth = _make_auth(_make_permission(Role.EDITOR))
    obj = make_object()
    with raises_app("E007004"):
        await auth.require_capability(Id(OTHER_ID), obj, AclCapability.DELETE)

async def test_no_acl_entry_denies_all_for_private_object():
    auth = _make_auth(None)
    obj = make_object(visibility=ObjectVisibility.PRIVATE)
    for cap in AclCapability:
        with raises_app("E007004"):
            await auth.require_capability(Id(OTHER_ID), obj, cap)
