"""
Integration tests — SqlAlchemyObjectRepository against real SQLite DB.
"""
import pytest
import pytest_asyncio

from app.common.constants.ObjectStatus import ObjectStatus
from app.common.util.IdGenerator import generate_id
from app.infrastructure.persistence.repository.object.SqlAlchemyObjectRepository import (
    SqlAlchemyObjectRepository,
)
from test.conftest import make_object
from test.integration.conftest import FakeSessionFactory

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def repo(db_session) -> SqlAlchemyObjectRepository:
    return SqlAlchemyObjectRepository(FakeSessionFactory(db_session))


# ── save + find_by_id ─────────────────────────────────────────────────────────

async def test_save_and_find_by_id(repo, db_session):
    obj = make_object(object_id=generate_id(), owner_identity_id=generate_id())

    await repo.save(obj)
    await db_session.flush()

    found = await repo.find_by_id(obj.object_id)
    assert found is not None
    assert found.object_id == obj.object_id
    assert found.owner_identity_id == obj.owner_identity_id
    assert found.status == ObjectStatus.ACTIVE

async def test_find_by_id_returns_none_for_unknown_id(repo):
    result = await repo.find_by_id(b'\xFF' * 24)
    assert result is None


# ── update ────────────────────────────────────────────────────────────────────

async def test_update_persists_status_change(repo, db_session):
    from datetime import datetime, timezone
    obj = make_object(object_id=generate_id(), owner_identity_id=generate_id())
    await repo.save(obj)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    archived = obj.archive(now)
    await repo.update(archived)
    await db_session.flush()

    found = await repo.find_by_id(obj.object_id)
    assert found is not None
    assert found.status == ObjectStatus.ARCHIVED


# ── exists ────────────────────────────────────────────────────────────────────

async def test_exists_returns_true_after_save(repo, db_session):
    obj = make_object(object_id=generate_id(), owner_identity_id=generate_id())
    await repo.save(obj)
    await db_session.flush()

    assert await repo.exists(obj.object_id)


async def test_exists_returns_false_for_unknown(repo):
    assert not await repo.exists(b'\x00' * 24)


# ── find_by_owner ─────────────────────────────────────────────────────────────

async def test_find_by_owner_returns_all_owned_objects(repo, db_session):
    owner = generate_id()
    obj_a = make_object(object_id=generate_id(), owner_identity_id=owner)
    obj_b = make_object(object_id=generate_id(), owner_identity_id=owner)
    other = make_object(object_id=generate_id(), owner_identity_id=generate_id())

    for o in (obj_a, obj_b, other):
        await repo.save(o)
    await db_session.flush()

    results = await repo.find_by_owner(owner)
    result_ids = {r.object_id for r in results}
    assert obj_a.object_id in result_ids
    assert obj_b.object_id in result_ids
    assert other.object_id not in result_ids
