"""
Unit tests — RestoreObjectUseCase:
  - SOFT_DELETED + owner → restored (ACTIVE)
  - ACTIVE → InvalidObjectStateException (can't restore active)
  - PURGED / not found → ObjectNotFoundException
  - non-owner → PermissionDeniedException
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dto.object.RestoreObjectCommand import RestoreObjectCommand
from app.application.usecase.object.RestoreObjectUseCase import RestoreObjectUseCase
from domain.object.valueobject.ObjectStatus import ObjectStatus
from app.common.exception.InvalidObjectStateException import InvalidObjectStateException
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.common.exception.PermissionDeniedException import PermissionDeniedException
from test.conftest import OBJECT_ID, OTHER_ID, OWNER_ID, make_object, mock_audit, mock_tx

pytestmark = pytest.mark.asyncio


def _cmd(requester: bytes = OWNER_ID) -> RestoreObjectCommand:
    return RestoreObjectCommand(
        requester_identity_id=requester,
        requester_subject_type="HUMAN",
        requester_name="test",
        object_id=OBJECT_ID,
    )


def _make_uc(*, obj=None):
    load = MagicMock()
    load.find_by_id = AsyncMock(return_value=obj)
    save = MagicMock()
    save.update = AsyncMock(return_value=None)
    uc = RestoreObjectUseCase(
        transaction=mock_tx(),
        load_object=load,
        save_object=save,
        audit_service=mock_audit(),
    )
    return uc, save


# ── Happy path ────────────────────────────────────────────────────────────────

async def test_restores_soft_deleted_object():
    uc, save = _make_uc(obj=make_object(status=ObjectStatus.SOFT_DELETED))
    await uc.execute(_cmd())
    save.update.assert_called_once()
    assert save.update.call_args.args[0].status == ObjectStatus.ACTIVE


async def test_records_audit_on_restore():
    audit = mock_audit()
    load = MagicMock()
    load.find_by_id = AsyncMock(return_value=make_object(status=ObjectStatus.SOFT_DELETED))
    save = MagicMock()
    save.update = AsyncMock()
    uc = RestoreObjectUseCase(
        transaction=mock_tx(),
        load_object=load,
        save_object=save,
        audit_service=audit,
    )
    await uc.execute(_cmd())
    audit.record.assert_called_once_with(OBJECT_ID, OWNER_ID, "HUMAN", "test", "RESTORE")


# ── Invalid transitions ───────────────────────────────────────────────────────

async def test_raises_invalid_state_for_active_object():
    # ACTIVE → ACTIVE is not a valid transition
    uc, _ = _make_uc(obj=make_object(status=ObjectStatus.ACTIVE))
    with pytest.raises(InvalidObjectStateException):
        await uc.execute(_cmd())


# ── Not found / PURGED ────────────────────────────────────────────────────────

async def test_raises_not_found_when_missing():
    uc, _ = _make_uc(obj=None)
    with pytest.raises(ObjectNotFoundException):
        await uc.execute(_cmd())


async def test_raises_not_found_for_purged():
    uc, _ = _make_uc(obj=make_object(status=ObjectStatus.PURGED))
    with pytest.raises(ObjectNotFoundException):
        await uc.execute(_cmd())


# ── Ownership check ───────────────────────────────────────────────────────────

async def test_raises_permission_denied_for_non_owner():
    uc, _ = _make_uc(obj=make_object(
        status=ObjectStatus.SOFT_DELETED,
        owner_identity_id=OWNER_ID,
    ))
    with pytest.raises(PermissionDeniedException):
        await uc.execute(_cmd(requester=OTHER_ID))
