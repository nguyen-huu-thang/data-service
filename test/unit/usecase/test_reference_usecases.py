"""
Unit tests — reference use cases (create / list / delete). Ports mocked; no DB.
"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from test._app_errors import raises_app

from app.application.dto.reference.CreateObjectReferenceCommand import CreateObjectReferenceCommand
from app.application.dto.reference.DeleteObjectReferenceCommand import DeleteObjectReferenceCommand
from app.application.dto.reference.ListObjectReferencesQuery import ListObjectReferencesQuery
from app.application.usecase.reference.CreateObjectReferenceUseCase import CreateObjectReferenceUseCase
from app.application.usecase.reference.DeleteObjectReferenceUseCase import DeleteObjectReferenceUseCase
from app.application.usecase.reference.ListObjectReferencesUseCase import ListObjectReferencesUseCase
from app.domain.object.model.ObjectReference import ObjectReference
from app.domain.object.valueobject.ResourceType import ResourceType
from app.domain.sharedkernel.model.Id import Id
from test.conftest import OBJECT_ID, OTHER_ID, OWNER_ID, PERM_ID, make_object, mock_audit, mock_auth, mock_tx

pytestmark = pytest.mark.asyncio

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
_APP = b"\x09" * 24


def _reference(object_id=OBJECT_ID) -> ObjectReference:
    return ObjectReference(
        reference_id=Id(PERM_ID),
        object_id=Id(object_id),
        application_identity_id=Id(_APP),
        application_name="shop",
        resource_type=ResourceType.PRODUCT,
        resource_id="prod-1",
        created_at=_NOW,
    )


# ── create ────────────────────────────────────────────────────────────────────

def _create_uc(*, obj=None, auth_allow=True):
    load = MagicMock(); load.find_by_id = AsyncMock(return_value=obj)
    repo = MagicMock(); repo.save = AsyncMock()
    uc = CreateObjectReferenceUseCase(mock_tx(), load, repo, mock_auth(allow=auth_allow), mock_audit())
    return uc, repo


def _cmd_create(resource_type="PRODUCT", requester=OWNER_ID):
    return CreateObjectReferenceCommand(
        Id(requester), "HUMAN", "t", Id(OBJECT_ID),
        Id(_APP), "shop", resource_type, "prod-1",
    )


async def test_create_reference_saves():
    uc, repo = _create_uc(obj=make_object())
    result = await uc.execute(_cmd_create())
    assert isinstance(result.reference_id, Id)
    repo.save.assert_called_once()


async def test_create_reference_invalid_resource_type():
    uc, repo = _create_uc(obj=make_object())
    with raises_app("E007001"):
        await uc.execute(_cmd_create(resource_type="NOPE"))
    repo.save.assert_not_called()


async def test_create_reference_not_found():
    uc, _ = _create_uc(obj=None)
    with raises_app("E067000"):
        await uc.execute(_cmd_create())


async def test_create_reference_permission_denied():
    uc, _ = _create_uc(obj=make_object(), auth_allow=False)
    with raises_app("E007004"):
        await uc.execute(_cmd_create(requester=OTHER_ID))


# ── list ──────────────────────────────────────────────────────────────────────

async def test_list_references_returns_repo_result():
    load = MagicMock(); load.find_by_id = AsyncMock(return_value=make_object())
    repo = MagicMock(); repo.find_by_object = AsyncMock(return_value=[_reference()])
    uc = ListObjectReferencesUseCase(load, repo, mock_auth())
    result = await uc.execute(ListObjectReferencesQuery(Id(OWNER_ID), "HUMAN", "t", Id(OBJECT_ID)))
    assert len(result) == 1


# ── delete ────────────────────────────────────────────────────────────────────

def _delete_uc(*, obj=None, reference=None):
    load = MagicMock(); load.find_by_id = AsyncMock(return_value=obj)
    repo = MagicMock()
    repo.find_by_id = AsyncMock(return_value=reference)
    repo.delete = AsyncMock()
    uc = DeleteObjectReferenceUseCase(mock_tx(), load, repo, mock_auth(), mock_audit())
    return uc, repo


def _cmd_delete():
    return DeleteObjectReferenceCommand(Id(OWNER_ID), "HUMAN", "t", Id(OBJECT_ID), Id(PERM_ID))


async def test_delete_reference_deletes():
    uc, repo = _delete_uc(obj=make_object(), reference=_reference())
    await uc.execute(_cmd_delete())
    repo.delete.assert_called_once()


async def test_delete_reference_missing_raises():
    uc, repo = _delete_uc(obj=make_object(), reference=None)
    with raises_app("E067000"):
        await uc.execute(_cmd_delete())
    repo.delete.assert_not_called()


async def test_delete_reference_wrong_object_raises():
    uc, repo = _delete_uc(obj=make_object(), reference=_reference(object_id=OTHER_ID))
    with raises_app("E067000"):
        await uc.execute(_cmd_delete())
    repo.delete.assert_not_called()
