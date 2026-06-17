"""
Unit tests — share use cases (create / list / revoke / resolve).
Ports mocked; no DB.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from test._app_errors import raises_app

from app.application.dto.share.CreateObjectShareCommand import CreateObjectShareCommand
from app.application.dto.share.ListObjectSharesQuery import ListObjectSharesQuery
from app.application.dto.share.ResolveObjectShareQuery import ResolveObjectShareQuery
from app.application.dto.share.RevokeObjectShareCommand import RevokeObjectShareCommand
from app.application.usecase.share.CreateObjectShareUseCase import CreateObjectShareUseCase
from app.application.usecase.share.ListObjectSharesUseCase import ListObjectSharesUseCase
from app.application.usecase.share.ResolveObjectShareUseCase import ResolveObjectShareUseCase
from app.application.usecase.share.RevokeObjectShareUseCase import RevokeObjectShareUseCase
from app.domain.object.model.ObjectShare import ObjectShare
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.sharedkernel.model.Id import Id
from test.conftest import OBJECT_ID, OTHER_ID, OWNER_ID, PERM_ID, make_object, mock_audit, mock_auth, mock_tx

pytestmark = pytest.mark.asyncio

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _share(object_id=OBJECT_ID, expires_at=None) -> ObjectShare:
    return ObjectShare(
        share_id=Id(PERM_ID),
        object_id=Id(object_id),
        share_token="tok-123",
        expires_at=expires_at,
        created_at=_NOW,
    )


# ── create ────────────────────────────────────────────────────────────────────

def _create_uc(*, obj=None, auth_allow=True):
    load = MagicMock(); load.find_by_id = AsyncMock(return_value=obj)
    repo = MagicMock(); repo.save = AsyncMock()
    uc = CreateObjectShareUseCase(mock_tx(), load, repo, mock_auth(allow=auth_allow), mock_audit())
    return uc, repo


def _cmd_create(requester=OWNER_ID):
    return CreateObjectShareCommand(Id(requester), "HUMAN", "t", Id(OBJECT_ID), None)


async def test_create_share_generates_token_and_saves():
    uc, repo = _create_uc(obj=make_object())
    result = await uc.execute(_cmd_create())
    assert result.share_token
    assert isinstance(result.share_id, Id)
    repo.save.assert_called_once()


async def test_create_share_not_found():
    uc, _ = _create_uc(obj=None)
    with raises_app("E067000"):
        await uc.execute(_cmd_create())


async def test_create_share_permission_denied():
    uc, _ = _create_uc(obj=make_object(), auth_allow=False)
    with raises_app("E007004"):
        await uc.execute(_cmd_create(requester=OTHER_ID))


# ── list ──────────────────────────────────────────────────────────────────────

async def test_list_shares_returns_repo_result():
    load = MagicMock(); load.find_by_id = AsyncMock(return_value=make_object())
    repo = MagicMock(); repo.find_by_object = AsyncMock(return_value=[_share()])
    uc = ListObjectSharesUseCase(load, repo, mock_auth())
    result = await uc.execute(ListObjectSharesQuery(Id(OWNER_ID), "HUMAN", "t", Id(OBJECT_ID)))
    assert len(result) == 1


# ── revoke ────────────────────────────────────────────────────────────────────

def _revoke_uc(*, obj=None, share=None):
    load = MagicMock(); load.find_by_id = AsyncMock(return_value=obj)
    repo = MagicMock()
    repo.find_by_id = AsyncMock(return_value=share)
    repo.delete = AsyncMock()
    uc = RevokeObjectShareUseCase(mock_tx(), load, repo, mock_auth(), mock_audit())
    return uc, repo


def _cmd_revoke():
    return RevokeObjectShareCommand(Id(OWNER_ID), "HUMAN", "t", Id(OBJECT_ID), Id(PERM_ID))


async def test_revoke_share_deletes():
    uc, repo = _revoke_uc(obj=make_object(), share=_share())
    await uc.execute(_cmd_revoke())
    repo.delete.assert_called_once()


async def test_revoke_share_missing_raises():
    uc, repo = _revoke_uc(obj=make_object(), share=None)
    with raises_app("E067000"):
        await uc.execute(_cmd_revoke())
    repo.delete.assert_not_called()


async def test_revoke_share_wrong_object_raises():
    uc, repo = _revoke_uc(obj=make_object(), share=_share(object_id=OTHER_ID))
    with raises_app("E067000"):
        await uc.execute(_cmd_revoke())
    repo.delete.assert_not_called()


# ── resolve ───────────────────────────────────────────────────────────────────

def _resolve_uc(*, share=None, obj=None):
    load = MagicMock(); load.find_by_id = AsyncMock(return_value=obj)
    repo = MagicMock(); repo.find_by_token = AsyncMock(return_value=share)
    return ResolveObjectShareUseCase(load, repo)


async def test_resolve_returns_object():
    obj = make_object()
    uc = _resolve_uc(share=_share(), obj=obj)
    assert await uc.execute(ResolveObjectShareQuery("tok-123")) is obj


async def test_resolve_unknown_token_raises():
    uc = _resolve_uc(share=None)
    with raises_app("E067000"):
        await uc.execute(ResolveObjectShareQuery("nope"))


async def test_resolve_expired_token_raises():
    expired = _share(expires_at=_NOW - timedelta(days=1))
    uc = _resolve_uc(share=expired, obj=make_object())
    with raises_app("E067000"):
        await uc.execute(ResolveObjectShareQuery("tok-123"))


async def test_resolve_deleted_object_raises():
    uc = _resolve_uc(share=_share(), obj=make_object(status=ObjectStatus.SOFT_DELETED))
    with raises_app("E067000"):
        await uc.execute(ResolveObjectShareQuery("tok-123"))
