"""
Unit tests — ListVersionsUseCase:
  - object found + authorized → returns list of versions
  - object not found / PURGED → ObjectNotFoundException
  - permission denied → PermissionDeniedException
  - empty list returned when no versions
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from test._app_errors import raises_app

from app.application.dto.version.ListVersionsQuery import ListVersionsQuery
from app.application.usecase.version.ListVersionsUseCase import ListVersionsUseCase
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from test.conftest import OBJECT_ID, OTHER_ID, OWNER_ID, make_object, make_version, mock_auth

pytestmark = pytest.mark.asyncio


def _query(requester: bytes = OWNER_ID) -> ListVersionsQuery:
    return ListVersionsQuery(
        requester_identity_id=requester,
        requester_subject_type="HUMAN",
        requester_name="test",
        object_id=OBJECT_ID,
    )


def _make_uc(*, obj=None, versions=None, auth_allow: bool = True):
    load_obj = MagicMock()
    load_obj.find_by_id = AsyncMock(return_value=obj)

    load_ver = MagicMock()
    load_ver.find_by_object = AsyncMock(return_value=versions if versions is not None else [])

    return ListVersionsUseCase(
        load_object=load_obj,
        load_version=load_ver,
        authorization_service=mock_auth(allow=auth_allow),
    )


# ── Happy path ────────────────────────────────────────────────────────────────

async def test_returns_all_versions():
    v1 = make_version(version_number=1)
    v2 = make_version(version_id=b"\x0c" * 24, version_number=2)
    uc = _make_uc(obj=make_object(), versions=[v1, v2])
    result = await uc.execute(_query())
    assert result == [v1, v2]


async def test_returns_empty_list_when_no_versions():
    uc = _make_uc(obj=make_object(), versions=[])
    result = await uc.execute(_query())
    assert result == []


# ── Not found / PURGED ────────────────────────────────────────────────────────

async def test_raises_not_found_when_object_missing():
    uc = _make_uc(obj=None)
    with raises_app("E067000"):
        await uc.execute(_query())


async def test_raises_not_found_for_purged_object():
    uc = _make_uc(obj=make_object(status=ObjectStatus.PURGED))
    with raises_app("E067000"):
        await uc.execute(_query())


# ── Permission denied ─────────────────────────────────────────────────────────

async def test_raises_permission_denied_when_unauthorized():
    uc = _make_uc(obj=make_object(), versions=[], auth_allow=False)
    with raises_app("E007004"):
        await uc.execute(_query(requester=OTHER_ID))
