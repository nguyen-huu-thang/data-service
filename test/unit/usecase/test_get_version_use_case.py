"""
Unit tests — GetVersionUseCase:
  - version found and belongs to object → returned
  - object not found / PURGED → ObjectNotFoundException
  - version not found → ObjectNotFoundException
  - version belongs to different object → ObjectNotFoundException (no info leak)
  - permission denied → PermissionDeniedException
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from test._app_errors import raises_app

from app.application.dto.version.GetVersionQuery import GetVersionQuery
from app.application.usecase.version.GetVersionUseCase import GetVersionUseCase
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.sharedkernel.model.Id import Id
from test.conftest import OBJECT_ID, OTHER_ID, OWNER_ID, VERSION_ID, make_object, make_version, mock_auth

pytestmark = pytest.mark.asyncio


def _query(requester: bytes = OWNER_ID) -> GetVersionQuery:
    return GetVersionQuery(
        requester_identity_id=Id(requester),
        requester_subject_type="HUMAN",
        requester_name="test",
        object_id=Id(OBJECT_ID),
        version_id=Id(VERSION_ID),
    )


def _make_uc(*, obj=None, version=None, auth_allow: bool = True):
    load_obj = MagicMock()
    load_obj.find_by_id = AsyncMock(return_value=obj)

    load_ver = MagicMock()
    load_ver.find_by_id = AsyncMock(return_value=version)

    return GetVersionUseCase(
        load_object=load_obj,
        load_version=load_ver,
        authorization_service=mock_auth(allow=auth_allow),
    )


# ── Happy path ────────────────────────────────────────────────────────────────

async def test_returns_version_when_found():
    v = make_version()
    uc = _make_uc(obj=make_object(), version=v)
    result = await uc.execute(_query())
    assert result is v


# ── Object not found ──────────────────────────────────────────────────────────

async def test_raises_not_found_when_object_missing():
    uc = _make_uc(obj=None, version=make_version())
    with raises_app("E067000"):
        await uc.execute(_query())


async def test_raises_not_found_for_purged_object():
    uc = _make_uc(obj=make_object(status=ObjectStatus.PURGED), version=make_version())
    with raises_app("E067000"):
        await uc.execute(_query())


# ── Version not found ─────────────────────────────────────────────────────────

async def test_raises_not_found_when_version_missing():
    uc = _make_uc(obj=make_object(), version=None)
    with raises_app("E067000"):
        await uc.execute(_query())


async def test_raises_not_found_when_version_belongs_to_different_object():
    # Version exists but object_id doesn't match — prevent info leak
    v = make_version(object_id=b"\xff" * 24)  # different object
    uc = _make_uc(obj=make_object(), version=v)
    with raises_app("E067000"):
        await uc.execute(_query())


# ── Permission denied ─────────────────────────────────────────────────────────

async def test_raises_permission_denied_when_unauthorized():
    uc = _make_uc(obj=make_object(), version=make_version(), auth_allow=False)
    with raises_app("E007004"):
        await uc.execute(_query(requester=OTHER_ID))
