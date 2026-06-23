"""
Unit tests — DownloadVersionUseCase:
  - version found + authorized → resolves storage pointer + metadata
  - object not found / PURGED → ObjectNotFoundException
  - version not found → ObjectNotFoundException
  - version belongs to different object → ObjectNotFoundException
  - permission denied → PermissionDeniedException

The use case no longer reads blob bytes (the adapter streams/loads them); it only
authorizes, audits and resolves the blob location + version metadata.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from test._app_errors import raises_app

from app.application.dto.version.DownloadVersionQuery import DownloadVersionQuery
from app.application.usecase.version.DownloadVersionUseCase import DownloadVersionUseCase
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.sharedkernel.model.Id import Id
from test.conftest import OBJECT_ID, OTHER_ID, OWNER_ID, VERSION_ID, make_object, make_version, mock_audit, mock_auth

pytestmark = pytest.mark.asyncio


def _query(requester: bytes = OWNER_ID) -> DownloadVersionQuery:
    return DownloadVersionQuery(
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

    return DownloadVersionUseCase(
        load_object=load_obj,
        load_version=load_ver,
        authorization_service=mock_auth(allow=auth_allow),
        audit_service=mock_audit(),
    )


# ── Happy path ────────────────────────────────────────────────────────────────

async def test_resolves_pointer_and_metadata():
    v = make_version()
    uc = _make_uc(obj=make_object(), version=v)
    result = await uc.execute(_query())
    assert result.storage_pointer == v.storage_pointer
    assert result.mime_type == "image/jpeg"
    assert result.content_hash == v.content_hash.value
    assert result.version_number == v.version_number


async def test_records_audit_on_download():
    audit = mock_audit()
    v = make_version()
    load_obj = MagicMock()
    load_obj.find_by_id = AsyncMock(return_value=make_object())
    load_ver = MagicMock()
    load_ver.find_by_id = AsyncMock(return_value=v)
    uc = DownloadVersionUseCase(
        load_object=load_obj,
        load_version=load_ver,
        authorization_service=mock_auth(),
        audit_service=audit,
    )
    await uc.execute(_query())
    audit.record.assert_called_once_with(Id(OBJECT_ID), Id(OWNER_ID), "HUMAN", "test", "DOWNLOAD_VERSION")


# ── Not found ─────────────────────────────────────────────────────────────────

async def test_raises_not_found_when_object_missing():
    uc = _make_uc(obj=None)
    with raises_app("E067000"):
        await uc.execute(_query())


async def test_raises_not_found_for_purged_object():
    uc = _make_uc(obj=make_object(status=ObjectStatus.PURGED))
    with raises_app("E067000"):
        await uc.execute(_query())


async def test_raises_not_found_when_version_missing():
    uc = _make_uc(obj=make_object(), version=None)
    with raises_app("E067000"):
        await uc.execute(_query())


async def test_raises_not_found_when_version_belongs_to_different_object():
    v = make_version(object_id=b"\xff" * 24)
    uc = _make_uc(obj=make_object(), version=v)
    with raises_app("E067000"):
        await uc.execute(_query())


# ── Permission denied ─────────────────────────────────────────────────────────

async def test_raises_permission_denied_when_unauthorized():
    uc = _make_uc(obj=make_object(), version=make_version(), auth_allow=False)
    with raises_app("E007004"):
        await uc.execute(_query(requester=OTHER_ID))
