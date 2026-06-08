"""
Unit tests — DownloadVersionUseCase:
  - version found + authorized → blob downloaded, result returned
  - object not found / PURGED → ObjectNotFoundException
  - version not found → ObjectNotFoundException
  - version belongs to different object → ObjectNotFoundException
  - permission denied → PermissionDeniedException
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dto.version.DownloadVersionQuery import DownloadVersionQuery
from app.application.usecase.version.DownloadVersionUseCase import DownloadVersionUseCase
from domain.object.valueobject.ObjectStatus import ObjectStatus
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.common.exception.PermissionDeniedException import PermissionDeniedException
from test.conftest import OBJECT_ID, OTHER_ID, OWNER_ID, VERSION_ID, make_object, make_version, mock_audit, mock_auth

pytestmark = pytest.mark.asyncio

_BLOB = b"version binary data"


def _query(requester: bytes = OWNER_ID) -> DownloadVersionQuery:
    return DownloadVersionQuery(
        requester_identity_id=requester,
        requester_subject_type="HUMAN",
        requester_name="test",
        object_id=OBJECT_ID,
        version_id=VERSION_ID,
    )


def _make_uc(*, obj=None, version=None, auth_allow: bool = True):
    load_obj = MagicMock()
    load_obj.find_by_id = AsyncMock(return_value=obj)

    load_ver = MagicMock()
    load_ver.find_by_id = AsyncMock(return_value=version)

    blob = MagicMock()
    blob.download = AsyncMock(return_value=_BLOB)

    return DownloadVersionUseCase(
        load_object=load_obj,
        load_version=load_ver,
        blob_storage=blob,
        authorization_service=mock_auth(allow=auth_allow),
        audit_service=mock_audit(),
    ), blob


# ── Happy path ────────────────────────────────────────────────────────────────

async def test_returns_blob_data_and_metadata():
    v = make_version()
    uc, _ = _make_uc(obj=make_object(), version=v)
    result = await uc.execute(_query())
    assert result.data == _BLOB
    assert result.mime_type == "image/jpeg"
    assert result.content_hash == v.content_hash.value
    assert result.version_number == v.version_number


async def test_downloads_from_version_storage_pointer():
    v = make_version()
    uc, blob = _make_uc(obj=make_object(), version=v)
    await uc.execute(_query())
    blob.download.assert_called_once_with(v.storage_pointer)


async def test_records_audit_on_download():
    audit = mock_audit()
    v = make_version()
    load_obj = MagicMock()
    load_obj.find_by_id = AsyncMock(return_value=make_object())
    load_ver = MagicMock()
    load_ver.find_by_id = AsyncMock(return_value=v)
    blob = MagicMock()
    blob.download = AsyncMock(return_value=_BLOB)
    uc = DownloadVersionUseCase(
        load_object=load_obj,
        load_version=load_ver,
        blob_storage=blob,
        authorization_service=mock_auth(),
        audit_service=audit,
    )
    await uc.execute(_query())
    audit.record.assert_called_once_with(OBJECT_ID, OWNER_ID, "HUMAN", "test", "DOWNLOAD_VERSION")


# ── Not found ─────────────────────────────────────────────────────────────────

async def test_raises_not_found_when_object_missing():
    uc, _ = _make_uc(obj=None)
    with pytest.raises(ObjectNotFoundException):
        await uc.execute(_query())


async def test_raises_not_found_for_purged_object():
    uc, _ = _make_uc(obj=make_object(status=ObjectStatus.PURGED))
    with pytest.raises(ObjectNotFoundException):
        await uc.execute(_query())


async def test_raises_not_found_when_version_missing():
    uc, _ = _make_uc(obj=make_object(), version=None)
    with pytest.raises(ObjectNotFoundException):
        await uc.execute(_query())


async def test_raises_not_found_when_version_belongs_to_different_object():
    v = make_version(object_id=b"\xff" * 24)
    uc, _ = _make_uc(obj=make_object(), version=v)
    with pytest.raises(ObjectNotFoundException):
        await uc.execute(_query())


# ── Permission denied ─────────────────────────────────────────────────────────

async def test_raises_permission_denied_when_unauthorized():
    uc, _ = _make_uc(obj=make_object(), version=make_version(), auth_allow=False)
    with pytest.raises(PermissionDeniedException):
        await uc.execute(_query(requester=OTHER_ID))
