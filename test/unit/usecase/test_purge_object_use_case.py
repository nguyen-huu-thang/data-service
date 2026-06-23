"""
Unit tests — PurgeObjectUseCase:
  - SOFT_DELETED + owner → blobs deleted, DB row marked PURGED
  - ACTIVE / ARCHIVED → InvalidObjectStateException
  - not found / already PURGED → ObjectNotFoundException
  - non-owner → PermissionDeniedException
  - blob delete failure is swallowed (object is still purged in DB)
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from test._app_errors import raises_app

from app.application.dto.object.PurgeObjectCommand import PurgeObjectCommand
from app.application.usecase.object.PurgeObjectUseCase import PurgeObjectUseCase
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.sharedkernel.model.Id import Id
from test.conftest import (
    OBJECT_ID, OTHER_ID, OWNER_ID, VERSION_ID,
    make_object, make_version, mock_audit, mock_storage, mock_tx,
)

pytestmark = pytest.mark.asyncio


def _cmd(requester: bytes = OWNER_ID) -> PurgeObjectCommand:
    return PurgeObjectCommand(
        requester_identity_id=Id(requester),
        requester_subject_type="HUMAN",
        requester_name="test",
        object_id=Id(OBJECT_ID),
    )


def _make_uc(*, obj=None, versions=None, blob_delete_raises=False):
    load_obj = MagicMock()
    load_obj.find_by_id = AsyncMock(return_value=obj)
    load_obj.find_by_id_for_update = AsyncMock(return_value=obj)

    load_ver = MagicMock()
    load_ver.find_by_object = AsyncMock(return_value=versions or [])

    save = MagicMock()
    save.update = AsyncMock(return_value=None)

    storage = mock_storage()
    if blob_delete_raises:
        storage.delete = AsyncMock(side_effect=Exception("blob error"))

    uc = PurgeObjectUseCase(
        transaction=mock_tx(),
        load_object=load_obj,
        save_object=save,
        load_version=load_ver,
        storage=storage,
        audit_service=mock_audit(),
    )
    return uc, save, storage


# ── Happy path ────────────────────────────────────────────────────────────────

async def test_marks_object_as_purged():
    v = make_version()
    uc, save, _ = _make_uc(obj=make_object(status=ObjectStatus.SOFT_DELETED), versions=[v])
    await uc.execute(_cmd())
    save.update.assert_called_once()
    assert save.update.call_args.args[0].status == ObjectStatus.PURGED


async def test_deletes_blob_for_each_version():
    v1 = make_version(version_id=VERSION_ID, version_number=1)
    v2 = make_version(version_id=b"\x0c" * 24, version_number=2)
    uc, _, storage = _make_uc(obj=make_object(status=ObjectStatus.SOFT_DELETED), versions=[v1, v2])
    await uc.execute(_cmd())
    assert storage.delete.call_count == 2


async def test_records_audit_on_purge():
    audit = mock_audit()
    load_obj = MagicMock()
    _purge_obj = make_object(status=ObjectStatus.SOFT_DELETED)
    load_obj.find_by_id = AsyncMock(return_value=_purge_obj)
    load_obj.find_by_id_for_update = AsyncMock(return_value=_purge_obj)
    load_ver = MagicMock()
    load_ver.find_by_object = AsyncMock(return_value=[])
    save = MagicMock()
    save.update = AsyncMock()
    storage = mock_storage()
    uc = PurgeObjectUseCase(
        transaction=mock_tx(),
        load_object=load_obj,
        save_object=save,
        load_version=load_ver,
        storage=storage,
        audit_service=audit,
    )
    await uc.execute(_cmd())
    audit.record.assert_called_once_with(Id(OBJECT_ID), Id(OWNER_ID), "HUMAN", "test", "PURGE")


async def test_blob_delete_failure_does_not_block_purge():
    v = make_version()
    uc, save, _ = _make_uc(
        obj=make_object(status=ObjectStatus.SOFT_DELETED),
        versions=[v],
        blob_delete_raises=True,
    )
    # Should NOT raise — blob errors are swallowed
    await uc.execute(_cmd())
    save.update.assert_called_once()


# ── Invalid transitions ───────────────────────────────────────────────────────

@pytest.mark.parametrize("bad_status", [ObjectStatus.ACTIVE, ObjectStatus.ARCHIVED])
async def test_raises_invalid_state_for_non_soft_deleted(bad_status):
    uc, _, _ = _make_uc(obj=make_object(status=bad_status))
    with raises_app("E067002"):
        await uc.execute(_cmd())


# ── Not found / PURGED ────────────────────────────────────────────────────────

async def test_raises_not_found_when_missing():
    uc, _, _ = _make_uc(obj=None)
    with raises_app("E067000"):
        await uc.execute(_cmd())


async def test_raises_not_found_for_already_purged():
    uc, _, _ = _make_uc(obj=make_object(status=ObjectStatus.PURGED))
    with raises_app("E067000"):
        await uc.execute(_cmd())


# ── Ownership check ───────────────────────────────────────────────────────────

async def test_raises_permission_denied_for_non_owner():
    uc, _, _ = _make_uc(obj=make_object(
        status=ObjectStatus.SOFT_DELETED,
        owner_identity_id=OWNER_ID,
    ))
    with raises_app("E007004"):
        await uc.execute(_cmd(requester=OTHER_ID))
