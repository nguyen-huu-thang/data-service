"""
Unit tests — DownloadObjectUseCase:
  - found + authorized → returns blob data with mime type from latest version
  - no current_version_id → uses default mime type "application/octet-stream"
  - not found / PURGED → ObjectNotFoundException
  - permission denied → PermissionDeniedException
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from test._app_errors import raises_app

from app.application.dto.object.DownloadObjectQuery import DownloadObjectQuery
from app.application.usecase.object.DownloadObjectUseCase import DownloadObjectUseCase
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from test.conftest import (
    OBJECT_ID, OTHER_ID, OWNER_ID, VERSION_ID,
    make_object, make_version, mock_audit, mock_auth, mock_tx,
)

pytestmark = pytest.mark.asyncio

_BLOB_DATA = b"fake binary content"


def _query(requester: bytes = OWNER_ID) -> DownloadObjectQuery:
    return DownloadObjectQuery(
        requester_identity_id=requester,
        requester_subject_type="HUMAN",
        requester_name="test",
        object_id=OBJECT_ID,
    )


def _make_uc(*, obj=None, version=None, auth_allow: bool = True):
    load_obj = MagicMock()
    load_obj.find_by_id = AsyncMock(return_value=obj)

    load_ver = MagicMock()
    load_ver.find_by_id = AsyncMock(return_value=version)

    blob = MagicMock()
    blob.download = AsyncMock(return_value=_BLOB_DATA)

    uc = DownloadObjectUseCase(
        transaction=mock_tx(),
        load_object=load_obj,
        load_version=load_ver,
        blob_storage=blob,
        authorization_service=mock_auth(allow=auth_allow),
        audit_service=mock_audit(),
    )
    return uc, blob


# ── Happy path ────────────────────────────────────────────────────────────────

async def test_returns_blob_data():
    v = make_version()
    obj = make_object(current_version_id=VERSION_ID)
    uc, _ = _make_uc(obj=obj, version=v)
    result = await uc.execute(_query())
    assert result.data == _BLOB_DATA
    assert result.content_size == len(_BLOB_DATA)


async def test_uses_mime_type_from_version():
    v = make_version()  # mime_type="image/jpeg"
    obj = make_object(current_version_id=VERSION_ID)
    uc, _ = _make_uc(obj=obj, version=v)
    result = await uc.execute(_query())
    assert result.mime_type == "image/jpeg"


async def test_uses_default_mime_when_no_current_version():
    obj = make_object(current_version_id=None)
    uc, _ = _make_uc(obj=obj, version=None)
    result = await uc.execute(_query())
    assert result.mime_type == "application/octet-stream"


async def test_records_audit_on_download():
    audit = mock_audit()
    v = make_version()
    obj = make_object(current_version_id=VERSION_ID)
    load_obj = MagicMock()
    load_obj.find_by_id = AsyncMock(return_value=obj)
    load_ver = MagicMock()
    load_ver.find_by_id = AsyncMock(return_value=v)
    blob = MagicMock()
    blob.download = AsyncMock(return_value=_BLOB_DATA)
    uc = DownloadObjectUseCase(
        transaction=mock_tx(),
        load_object=load_obj,
        load_version=load_ver,
        blob_storage=blob,
        authorization_service=mock_auth(),
        audit_service=audit,
    )
    await uc.execute(_query())
    audit.record.assert_called_once_with(OBJECT_ID, OWNER_ID, "HUMAN", "test", "DOWNLOAD")


# ── Not found / PURGED ────────────────────────────────────────────────────────

async def test_raises_not_found_when_object_missing():
    uc, _ = _make_uc(obj=None)
    with raises_app("E067000"):
        await uc.execute(_query())


async def test_raises_not_found_for_purged_object():
    uc, _ = _make_uc(obj=make_object(status=ObjectStatus.PURGED))
    with raises_app("E067000"):
        await uc.execute(_query())


# ── Permission denied ─────────────────────────────────────────────────────────

async def test_raises_permission_denied_when_unauthorized():
    uc, _ = _make_uc(obj=make_object(), auth_allow=False)
    with raises_app("E007004"):
        await uc.execute(_query(requester=OTHER_ID))
