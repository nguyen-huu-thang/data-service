"""
Unit tests — DeleteObjectUseCase:
  - active object + owner → soft-deleted, saved, audit recorded
  - not found / PURGED → ObjectNotFoundException
  - already deleted (SOFT_DELETED or PURGED) → ObjectAlreadyDeletedException
  - permission denied → PermissionDeniedException
"""
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from app.application.dto.object.DeleteObjectCommand import DeleteObjectCommand
from app.application.usecase.object.DeleteObjectUseCase import DeleteObjectUseCase
from domain.object.valueobject.ObjectStatus import ObjectStatus
from app.common.exception.ObjectAlreadyDeletedException import ObjectAlreadyDeletedException
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.common.exception.PermissionDeniedException import PermissionDeniedException
from test.conftest import OBJECT_ID, OTHER_ID, OWNER_ID, make_object, mock_audit, mock_auth, mock_tx

pytestmark = pytest.mark.asyncio


def _cmd(requester: bytes = OWNER_ID) -> DeleteObjectCommand:
    return DeleteObjectCommand(
        requester_identity_id=requester,
        requester_subject_type="HUMAN",
        requester_name="test",
        object_id=OBJECT_ID,
    )


def _make_uc(*, obj=None, auth_allow: bool = True):
    load = MagicMock()
    load.find_by_id = AsyncMock(return_value=obj)
    save = MagicMock()
    save.update = AsyncMock(return_value=None)
    uc = DeleteObjectUseCase(
        transaction=mock_tx(),
        load_object=load,
        save_object=save,
        authorization_service=mock_auth(allow=auth_allow),
        audit_service=mock_audit(),
    )
    return uc, save


# ── Happy path ────────────────────────────────────────────────────────────────

async def test_soft_deletes_active_object():
    uc, save = _make_uc(obj=make_object(status=ObjectStatus.ACTIVE))
    await uc.execute(_cmd())
    save.update.assert_called_once()
    saved_obj = save.update.call_args.args[0]
    assert saved_obj.status == ObjectStatus.SOFT_DELETED


async def test_records_audit_on_delete():
    audit = mock_audit()
    load = MagicMock()
    load.find_by_id = AsyncMock(return_value=make_object())
    save = MagicMock()
    save.update = AsyncMock()
    uc = DeleteObjectUseCase(
        transaction=mock_tx(),
        load_object=load,
        save_object=save,
        authorization_service=mock_auth(),
        audit_service=audit,
    )
    await uc.execute(_cmd())
    audit.record.assert_called_once_with(OBJECT_ID, OWNER_ID, "HUMAN", "test", "DELETE")


# ── Not found ─────────────────────────────────────────────────────────────────

async def test_raises_not_found_when_object_missing():
    uc, _ = _make_uc(obj=None)
    with pytest.raises(ObjectNotFoundException):
        await uc.execute(_cmd())


async def test_raises_not_found_for_purged_object():
    uc, _ = _make_uc(obj=make_object(status=ObjectStatus.PURGED))
    with pytest.raises(ObjectNotFoundException):
        await uc.execute(_cmd())


# ── Already deleted ───────────────────────────────────────────────────────────

async def test_raises_already_deleted_for_soft_deleted_object():
    uc, _ = _make_uc(obj=make_object(status=ObjectStatus.SOFT_DELETED))
    with pytest.raises(ObjectAlreadyDeletedException):
        await uc.execute(_cmd())


# ── Permission denied ─────────────────────────────────────────────────────────

async def test_raises_permission_denied_when_unauthorized():
    uc, _ = _make_uc(obj=make_object(), auth_allow=False)
    with pytest.raises(PermissionDeniedException):
        await uc.execute(_cmd(requester=OTHER_ID))
