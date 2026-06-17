"""
Integration tests — SqlAlchemyPermissionRepository against real SQLite DB.
"""
from datetime import datetime, timezone

import pytest
import pytest_asyncio

from app.domain.permission.role.Role import Role
from app.domain.sharedkernel.factory.IdFactory import IdFactory
from app.domain.sharedkernel.model.Id import Id
from app.domain.permission.model.ObjectPermission import ObjectPermission
from app.infrastructure.persistence.repository.object.SqlAlchemyObjectRepository import (
    SqlAlchemyObjectRepository,
)
from app.infrastructure.persistence.repository.permission.SqlAlchemyPermissionRepository import (
    SqlAlchemyPermissionRepository,
)
from test.conftest import make_object
from test.integration.conftest import FakeSessionFactory

pytestmark = pytest.mark.asyncio

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _make_permission(object_id: Id, subject_id: Id, role: Role) -> ObjectPermission:
    return ObjectPermission(
        permission_id=IdFactory.generate(),
        object_id=object_id,
        subject_identity_id=subject_id,
        subject_type="HUMAN",
        role=role,
        created_at=_NOW,
    )


@pytest_asyncio.fixture
async def repos(db_session):
    sf = FakeSessionFactory(db_session)
    obj_repo  = SqlAlchemyObjectRepository(sf)
    perm_repo = SqlAlchemyPermissionRepository(sf)
    return obj_repo, perm_repo


@pytest_asyncio.fixture
async def saved_object(repos, db_session):
    obj_repo, _ = repos
    owner_id  = IdFactory.generate()
    obj = make_object(object_id=IdFactory.generate(), owner_identity_id=owner_id)
    await obj_repo.save(obj)
    await db_session.flush()
    return obj


# ── save + find ───────────────────────────────────────────────────────────────

async def test_save_and_find_by_subject_and_object(repos, db_session, saved_object):
    _, perm_repo = repos
    subject_id = IdFactory.generate()
    perm = _make_permission(saved_object.object_id, subject_id, Role.VIEWER)

    await perm_repo.save(perm)
    await db_session.flush()

    found = await perm_repo.find_by_subject_and_object(subject_id, saved_object.object_id)
    assert found is not None
    assert found.role == Role.VIEWER
    assert found.subject_identity_id == subject_id


async def test_find_by_subject_and_object_returns_none_when_absent(repos, saved_object):
    _, perm_repo = repos
    result = await perm_repo.find_by_subject_and_object(IdFactory.generate(), saved_object.object_id)
    assert result is None


async def test_find_by_object_returns_all_permissions(repos, db_session, saved_object):
    _, perm_repo = repos
    subj_a = IdFactory.generate()
    subj_b = IdFactory.generate()

    await perm_repo.save(_make_permission(saved_object.object_id, subj_a, Role.EDITOR))
    await perm_repo.save(_make_permission(saved_object.object_id, subj_b, Role.VIEWER))
    await db_session.flush()

    perms = await perm_repo.find_by_object(saved_object.object_id)
    subjects = {p.subject_identity_id for p in perms}
    assert subj_a in subjects
    assert subj_b in subjects


# ── delete ────────────────────────────────────────────────────────────────────

async def test_delete_removes_permission(repos, db_session, saved_object):
    _, perm_repo = repos
    subject_id = IdFactory.generate()
    perm = _make_permission(saved_object.object_id, subject_id, Role.EDITOR)

    await perm_repo.save(perm)
    await db_session.flush()

    await perm_repo.delete(perm.permission_id)
    await db_session.flush()

    result = await perm_repo.find_by_subject_and_object(subject_id, saved_object.object_id)
    assert result is None


async def test_delete_all_by_object_removes_all(repos, db_session, saved_object):
    _, perm_repo = repos

    await perm_repo.save(_make_permission(saved_object.object_id, IdFactory.generate(), Role.EDITOR))
    await perm_repo.save(_make_permission(saved_object.object_id, IdFactory.generate(), Role.VIEWER))
    await db_session.flush()

    await perm_repo.delete_all_by_object(saved_object.object_id)
    await db_session.flush()

    remaining = await perm_repo.find_by_object(saved_object.object_id)
    assert remaining == []
