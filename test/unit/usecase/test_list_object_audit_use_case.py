"""
Unit tests — ListObjectAuditUseCase:
  - authorized + object exists → audit list returned
  - object not found / PURGED → ObjectNotFoundException
  - permission denied → PermissionDeniedException
"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from test._app_errors import raises_app

from app.application.dto.audit.ListObjectAuditQuery import ListObjectAuditQuery
from app.application.usecase.audit.ListObjectAuditUseCase import ListObjectAuditUseCase
from app.domain.audit.model.ObjectAudit import ObjectAudit
from app.domain.audit.valueobject.AuditAction import AuditAction
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.sharedkernel.model.Id import Id
from test.conftest import OBJECT_ID, OTHER_ID, OWNER_ID, PERM_ID, make_object, mock_auth

pytestmark = pytest.mark.asyncio

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _query(requester: bytes = OWNER_ID) -> ListObjectAuditQuery:
    return ListObjectAuditQuery(
        requester_identity_id=Id(requester),
        requester_subject_type="HUMAN",
        requester_name="test",
        object_id=Id(OBJECT_ID),
    )


def _audit() -> ObjectAudit:
    return ObjectAudit(
        audit_id=Id(PERM_ID),
        object_id=Id(OBJECT_ID),
        actor_identity_id=Id(OWNER_ID),
        actor_subject_type="HUMAN",
        actor_name="test",
        action=AuditAction.CREATE,
        created_at=_NOW,
    )


def _make_uc(*, obj=None, audits=None, auth_allow: bool = True):
    load_obj = MagicMock()
    load_obj.find_by_id = AsyncMock(return_value=obj)
    load_audit = MagicMock()
    load_audit.find_by_object = AsyncMock(return_value=audits or [])
    return ListObjectAuditUseCase(
        load_object=load_obj,
        load_audit=load_audit,
        authorization_service=mock_auth(allow=auth_allow),
    )


async def test_returns_audit_list_when_authorized():
    entry = _audit()
    uc = _make_uc(obj=make_object(), audits=[entry])
    result = await uc.execute(_query())
    assert result == [entry]


async def test_raises_not_found_when_object_missing():
    uc = _make_uc(obj=None)
    with raises_app("E067000"):
        await uc.execute(_query())


async def test_raises_not_found_for_purged_object():
    uc = _make_uc(obj=make_object(status=ObjectStatus.PURGED))
    with raises_app("E067000"):
        await uc.execute(_query())


async def test_raises_permission_denied_when_unauthorized():
    uc = _make_uc(obj=make_object(), audits=[_audit()], auth_allow=False)
    with raises_app("E007004"):
        await uc.execute(_query(requester=OTHER_ID))
