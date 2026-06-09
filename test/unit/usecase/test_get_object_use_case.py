"""
Unit tests — GetObjectUseCase:
  - found + authorized → returns DataObject + records audit
  - object not found → ObjectNotFoundException
  - PURGED object → ObjectNotFoundException
  - permission denied → PermissionDeniedException (propagated from auth)
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dto.object.GetObjectQuery import GetObjectQuery
from app.application.usecase.object.GetObjectUseCase import GetObjectUseCase
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.common.exception.PermissionDeniedException import PermissionDeniedException
from test.conftest import OBJECT_ID, OTHER_ID, OWNER_ID, make_object, mock_audit, mock_auth, mock_tx

pytestmark = pytest.mark.asyncio


def _make_use_case(*, obj=None, auth_allow: bool = True) -> GetObjectUseCase:
    load = MagicMock()
    load.find_by_id = AsyncMock(return_value=obj)
    return GetObjectUseCase(
        transaction=mock_tx(),
        load_object=load,
        authorization_service=mock_auth(allow=auth_allow),
        audit_service=mock_audit(),
    )


def _query(requester: bytes = OWNER_ID) -> GetObjectQuery:
    return GetObjectQuery(
        requester_identity_id=requester,
        requester_subject_type="HUMAN",
        requester_name="test",
        object_id=OBJECT_ID,
    )


# ── Happy path ────────────────────────────────────────────────────────────────

async def test_returns_object_when_found_and_authorized():
    obj = make_object()
    uc = _make_use_case(obj=obj)
    result = await uc.execute(_query())
    assert result is obj


async def test_records_audit_on_success():
    obj = make_object()
    audit = mock_audit()
    load = MagicMock()
    load.find_by_id = AsyncMock(return_value=obj)
    uc = GetObjectUseCase(
        transaction=mock_tx(),
        load_object=load,
        authorization_service=mock_auth(),
        audit_service=audit,
    )
    await uc.execute(_query())
    audit.record.assert_called_once_with(obj.object_id, OWNER_ID, "HUMAN", "test", "READ")


# ── Not found ─────────────────────────────────────────────────────────────────

async def test_raises_not_found_when_object_missing():
    uc = _make_use_case(obj=None)
    with pytest.raises(ObjectNotFoundException):
        await uc.execute(_query())


async def test_raises_not_found_for_purged_object():
    uc = _make_use_case(obj=make_object(status=ObjectStatus.PURGED))
    with pytest.raises(ObjectNotFoundException):
        await uc.execute(_query())


# ── Permission denied ─────────────────────────────────────────────────────────

async def test_raises_permission_denied_when_unauthorized():
    uc = _make_use_case(obj=make_object(), auth_allow=False)
    with pytest.raises(PermissionDeniedException):
        await uc.execute(_query(requester=OTHER_ID))
