"""
Integration tests — SqlAlchemyVersionRepository against real SQLite DB.
"""
import pytest
import pytest_asyncio

from app.domain.sharedkernel.factory.IdFactory import IdFactory
from app.domain.sharedkernel.model.Id import Id
from app.infrastructure.persistence.repository.object.SqlAlchemyObjectRepository import (
    SqlAlchemyObjectRepository,
)
from app.infrastructure.persistence.repository.version.SqlAlchemyVersionRepository import (
    SqlAlchemyVersionRepository,
)
from test.conftest import make_object, make_version
from test.integration.conftest import FakeSessionFactory

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def repos(db_session):
    sf = FakeSessionFactory(db_session)
    return (
        SqlAlchemyObjectRepository(sf),
        SqlAlchemyVersionRepository(sf),
    )


@pytest_asyncio.fixture
async def saved_object(repos, db_session):
    obj_repo, _ = repos
    obj = make_object(object_id=IdFactory.generate().to_bytes(), owner_identity_id=IdFactory.generate().to_bytes())
    await obj_repo.save(obj)
    await db_session.flush()
    return obj


# ── save + find_by_id ─────────────────────────────────────────────────────────

async def test_save_and_find_by_id(repos, db_session, saved_object):
    _, ver_repo = repos
    v = make_version(version_id=IdFactory.generate().to_bytes(), object_id=saved_object.object_id)
    await ver_repo.save(v)
    await db_session.flush()

    found = await ver_repo.find_by_id(v.version_id)
    assert found is not None
    assert found.version_id == v.version_id
    assert found.object_id == saved_object.object_id
    assert found.version_number == 1


async def test_find_by_id_returns_none_for_unknown(repos):
    _, ver_repo = repos
    result = await ver_repo.find_by_id(Id(b"\xff" * 24))
    assert result is None


# ── find_by_object ────────────────────────────────────────────────────────────

async def test_find_by_object_returns_versions_in_order(repos, db_session, saved_object):
    _, ver_repo = repos
    v1 = make_version(version_id=IdFactory.generate().to_bytes(), object_id=saved_object.object_id, version_number=1)
    v2 = make_version(version_id=IdFactory.generate().to_bytes(), object_id=saved_object.object_id, version_number=2)
    v3 = make_version(version_id=IdFactory.generate().to_bytes(), object_id=saved_object.object_id, version_number=3)

    # Insert out of order to verify ordering
    for v in (v2, v3, v1):
        await ver_repo.save(v)
    await db_session.flush()

    versions = await ver_repo.find_by_object(saved_object.object_id)
    assert [v.version_number for v in versions] == [1, 2, 3]


async def test_find_by_object_returns_empty_for_unknown_object(repos):
    _, ver_repo = repos
    result = await ver_repo.find_by_object(Id(b"\xff" * 24))
    assert result == []


# ── find_latest_by_object ─────────────────────────────────────────────────────

async def test_find_latest_returns_highest_version_number(repos, db_session, saved_object):
    _, ver_repo = repos
    v1 = make_version(version_id=IdFactory.generate().to_bytes(), object_id=saved_object.object_id, version_number=1)
    v2 = make_version(version_id=IdFactory.generate().to_bytes(), object_id=saved_object.object_id, version_number=2)
    await ver_repo.save(v1)
    await ver_repo.save(v2)
    await db_session.flush()

    latest = await ver_repo.find_latest_by_object(saved_object.object_id)
    assert latest is not None
    assert latest.version_number == 2


async def test_find_latest_returns_none_for_object_with_no_versions(repos, saved_object):
    _, ver_repo = repos
    result = await ver_repo.find_latest_by_object(saved_object.object_id)
    assert result is None


# ── count_by_object ───────────────────────────────────────────────────────────

async def test_count_by_object_returns_correct_count(repos, db_session, saved_object):
    _, ver_repo = repos
    for i in range(3):
        v = make_version(version_id=IdFactory.generate().to_bytes(), object_id=saved_object.object_id, version_number=i + 1)
        await ver_repo.save(v)
    await db_session.flush()

    count = await ver_repo.count_by_object(saved_object.object_id)
    assert count == 3


async def test_count_by_object_returns_zero_when_no_versions(repos, saved_object):
    _, ver_repo = repos
    count = await ver_repo.count_by_object(saved_object.object_id)
    assert count == 0
