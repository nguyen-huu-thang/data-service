"""
Unit tests — ArchiveObjectUseCase:
  - ACTIVE object → archived and saved
  - ARCHIVED object → InvalidObjectStateException (already archived, can unarchive but not re-archive)
  - SOFT_DELETED → InvalidObjectStateException
  - PURGED / not found → ObjectNotFoundException
  - permission denied → PermissionDeniedException
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dto.object.ArchiveObjectCommand import ArchiveObjectCommand
from app.application.usecase.object.ArchiveObjectUseCase import ArchiveObjectUseCase
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.common.exception.InvalidObjectStateException import InvalidObjectStateException
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.common.exception.PermissionDeniedException import PermissionDeniedException
from test.conftest import OBJECT_ID, OTHER_ID, OWNER_ID, make_object, mock_audit, mock_auth, mock_tx

pytestmark = pytest.mark.asyncio


def _cmd(requester: bytes = OWNER_ID) -> ArchiveObjectCommand:
    return ArchiveObjectCommand(
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
    uc = ArchiveObjectUseCase(
        transaction=mock_tx(),
        load_object=load,
        save_object=save,
        authorization_service=mock_auth(allow=auth_allow),
        audit_service=mock_audit(),
    )
    return uc, save


# ── Happy path ────────────────────────────────────────────────────────────────

async def test_archives_active_object():
    uc, save = _make_uc(obj=make_object(status=ObjectStatus.ACTIVE))
    await uc.execute(_cmd())
    save.update.assert_called_once()
    assert save.update.call_args.args[0].status == ObjectStatus.ARCHIVED


async def test_records_audit_on_archive():
    audit = mock_audit()
    load = MagicMock()
    load.find_by_id = AsyncMock(return_value=make_object())
    save = MagicMock()
    save.update = AsyncMock()
    uc = ArchiveObjectUseCase(
        transaction=mock_tx(),
        load_object=load,
        save_object=save,
        authorization_service=mock_auth(),
        audit_service=audit,
    )
    await uc.execute(_cmd())
    audit.record.assert_called_once_with(OBJECT_ID, OWNER_ID, "HUMAN", "test", "ARCHIVE")


# ── Invalid transitions ───────────────────────────────────────────────────────

@pytest.mark.parametrize("bad_status", [ObjectStatus.SOFT_DELETED, ObjectStatus.PURGED])
async def test_raises_invalid_state_for_non_archivable_status(bad_status):
    # SOFT_DELETED → ARCHIVED is not allowed per state machine
    # PURGED is also caught as not-found first, but SOFT_DELETED hits invalid state
    if bad_status == ObjectStatus.PURGED:
        uc, _ = _make_uc(obj=make_object(status=bad_status))
        with pytest.raises(ObjectNotFoundException):
            await uc.execute(_cmd())
    else:
        uc, _ = _make_uc(obj=make_object(status=bad_status))
        with pytest.raises(InvalidObjectStateException):
            await uc.execute(_cmd())


# ── Not found ─────────────────────────────────────────────────────────────────

async def test_raises_not_found_when_missing():
    uc, _ = _make_uc(obj=None)
    with pytest.raises(ObjectNotFoundException):
        await uc.execute(_cmd())


# ── Permission denied ─────────────────────────────────────────────────────────

async def test_raises_permission_denied_when_unauthorized():
    uc, _ = _make_uc(obj=make_object(), auth_allow=False)
    with pytest.raises(PermissionDeniedException):
        await uc.execute(_cmd(requester=OTHER_ID))
