"""
Integration tests — SqlAlchemyAuditRepository against real SQLite DB:
  - save + find_by_object (ordered by created_at)
  - subject-level audit with object_id = None persists and is excluded from
    an object's trail
"""
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio

from app.domain.audit.model.ObjectAudit import ObjectAudit
from app.domain.audit.valueobject.AuditAction import AuditAction
from app.domain.sharedkernel.factory.IdFactory import IdFactory
from app.domain.sharedkernel.model.Id import Id
from app.infrastructure.persistence.repository.audit.SqlAlchemyAuditRepository import (
    SqlAlchemyAuditRepository,
)
from test.integration.conftest import FakeSessionFactory

pytestmark = pytest.mark.asyncio

_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest_asyncio.fixture
async def repo(db_session) -> SqlAlchemyAuditRepository:
    return SqlAlchemyAuditRepository(FakeSessionFactory(db_session))


def _audit(object_id, action: AuditAction, created_at: datetime) -> ObjectAudit:
    return ObjectAudit(
        audit_id=IdFactory.generate(),
        object_id=object_id,
        actor_identity_id=IdFactory.generate(),
        actor_subject_type="HUMAN",
        actor_name="test",
        action=action,
        created_at=created_at,
    )


async def test_save_and_find_by_object_ordered(repo, db_session):
    obj_id = IdFactory.generate()
    a2 = _audit(obj_id, AuditAction.READ, _T0 + timedelta(minutes=2))
    a1 = _audit(obj_id, AuditAction.CREATE, _T0)

    await repo.save(a2)
    await repo.save(a1)
    await db_session.flush()

    found = await repo.find_by_object(obj_id)
    assert [a.action for a in found] == [AuditAction.CREATE, AuditAction.READ]


async def test_find_by_object_excludes_other_objects(repo, db_session):
    obj_a = IdFactory.generate()
    obj_b = IdFactory.generate()
    await repo.save(_audit(obj_a, AuditAction.CREATE, _T0))
    await repo.save(_audit(obj_b, AuditAction.CREATE, _T0))
    await db_session.flush()

    found = await repo.find_by_object(obj_a)
    assert len(found) == 1
    assert found[0].object_id == obj_a


async def test_subject_level_audit_persists_with_null_object_id(repo, db_session):
    # Subject-level action: object_id is None.
    audit = _audit(None, AuditAction.SYNC_SUBJECT, _T0)
    await repo.save(audit)
    await db_session.flush()

    # Not attached to any object trail.
    assert await repo.find_by_object(IdFactory.generate()) == []
