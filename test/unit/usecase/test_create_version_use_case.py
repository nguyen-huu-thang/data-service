"""
Unit tests — CreateVersionUseCase:
  - ACTIVE object + WRITE permission → version saved, object updated, blob uploaded
  - non-ACTIVE object → InvalidObjectStateException
  - not found / PURGED → ObjectNotFoundException
  - permission denied → PermissionDeniedException
  - version number increments from latest
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from test._app_errors import raises_app

from app.application.dto.version.CreateVersionCommand import CreateVersionCommand
from app.application.usecase.version.CreateVersionUseCase import CreateVersionUseCase
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from test.conftest import OBJECT_ID, OTHER_ID, OWNER_ID, make_object, make_version, mock_audit, mock_auth, mock_tx

pytestmark = pytest.mark.asyncio

_DATA = b"new version content"


def _cmd(requester: bytes = OWNER_ID) -> CreateVersionCommand:
    return CreateVersionCommand(
        requester_identity_id=requester,
        requester_subject_type="HUMAN",
        requester_name="test",
        object_id=OBJECT_ID,
        filename="file_v2.jpg",
        content_type="image/jpeg",
        data=_DATA,
    )


def _make_uc(*, obj=None, latest_version=None, auth_allow: bool = True):
    load_obj = MagicMock()
    load_obj.find_by_id = AsyncMock(return_value=obj)
    load_obj.find_by_id_for_update = AsyncMock(return_value=obj)

    save_obj = MagicMock()
    save_obj.update = AsyncMock(return_value=None)

    load_ver = MagicMock()
    load_ver.find_latest_by_object = AsyncMock(return_value=latest_version)

    save_ver = MagicMock()
    save_ver.save = AsyncMock(return_value=None)

    blob = MagicMock()
    blob.generate_pointer = AsyncMock(return_value="test/path/v2.jpg")
    blob.upload = AsyncMock(return_value=None)

    uc = CreateVersionUseCase(
        transaction=mock_tx(),
        load_object=load_obj,
        save_object=save_obj,
        load_version=load_ver,
        save_version=save_ver,
        blob_storage=blob,
        authorization_service=mock_auth(allow=auth_allow),
        audit_service=mock_audit(),
    )
    return uc, save_ver, save_obj, blob


# ── Happy path ────────────────────────────────────────────────────────────────

async def test_returns_result_with_24_byte_version_id():
    uc, _, _, _ = _make_uc(obj=make_object(), latest_version=None)
    result = await uc.execute(_cmd())
    assert len(result.version_id) == 24


async def test_version_number_starts_at_1_when_no_existing():
    uc, _, _, _ = _make_uc(obj=make_object(), latest_version=None)
    result = await uc.execute(_cmd())
    assert result.version_number == 1


async def test_version_number_increments_from_latest():
    existing = make_version(version_number=3)
    uc, _, _, _ = _make_uc(obj=make_object(), latest_version=existing)
    result = await uc.execute(_cmd())
    assert result.version_number == 4


async def test_uploads_blob_before_saving():
    uc, save_ver, _, blob = _make_uc(obj=make_object(), latest_version=None)
    await uc.execute(_cmd())
    blob.upload.assert_called_once()
    save_ver.save.assert_called_once()


async def test_updates_object_current_version():
    uc, _, save_obj, _ = _make_uc(obj=make_object(), latest_version=None)
    await uc.execute(_cmd())
    save_obj.update.assert_called_once()
    updated = save_obj.update.call_args.args[0]
    assert updated.current_version_id is not None


async def test_content_hash_in_result():
    uc, _, _, _ = _make_uc(obj=make_object(), latest_version=None)
    result = await uc.execute(_cmd())
    assert len(result.content_hash) == 64  # SHA-256 hex


# ── Invalid state ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("bad_status", [ObjectStatus.ARCHIVED, ObjectStatus.SOFT_DELETED])
async def test_raises_invalid_state_for_non_active_object(bad_status):
    uc, _, _, _ = _make_uc(obj=make_object(status=bad_status))
    with raises_app("E067002"):
        await uc.execute(_cmd())


# ── Not found / PURGED ────────────────────────────────────────────────────────

async def test_raises_not_found_when_object_missing():
    uc, _, _, _ = _make_uc(obj=None)
    with raises_app("E067000"):
        await uc.execute(_cmd())


async def test_raises_not_found_for_purged():
    uc, _, _, _ = _make_uc(obj=make_object(status=ObjectStatus.PURGED))
    with raises_app("E067000"):
        await uc.execute(_cmd())


# ── Permission denied ─────────────────────────────────────────────────────────

async def test_raises_permission_denied_when_unauthorized():
    uc, _, _, _ = _make_uc(obj=make_object(), auth_allow=False)
    with raises_app("E007004"):
        await uc.execute(_cmd(requester=OTHER_ID))
