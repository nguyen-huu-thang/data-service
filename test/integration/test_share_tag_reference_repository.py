"""
Integration tests — share / tag / reference repositories against real SQLite.
Exercises Id <-> bytes mapping, find_by_token / find_by_object, tag replace.
"""
from datetime import datetime, timezone

import pytest
import pytest_asyncio

from app.domain.object.model.ObjectReference import ObjectReference
from app.domain.object.model.ObjectShare import ObjectShare
from app.domain.object.valueobject.ObjectTag import ObjectTag
from app.domain.object.valueobject.ResourceType import ResourceType
from app.domain.sharedkernel.factory.IdFactory import IdFactory
from app.infrastructure.persistence.repository.reference.SqlAlchemyObjectReferenceRepository import (
    SqlAlchemyObjectReferenceRepository,
)
from app.infrastructure.persistence.repository.share.SqlAlchemyObjectShareRepository import (
    SqlAlchemyObjectShareRepository,
)
from app.infrastructure.persistence.repository.tag.SqlAlchemyObjectTagRepository import (
    SqlAlchemyObjectTagRepository,
)
from test.integration.conftest import FakeSessionFactory

pytestmark = pytest.mark.asyncio

_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


# ── share ─────────────────────────────────────────────────────────────────────

async def test_share_save_find_by_token_and_object(db_session):
    repo = SqlAlchemyObjectShareRepository(FakeSessionFactory(db_session))
    obj_id = IdFactory.generate()
    share = ObjectShare(
        share_id=IdFactory.generate(),
        object_id=obj_id,
        share_token="token-abc",
        expires_at=None,
        created_at=_T0,
    )
    await repo.save(share)
    await db_session.flush()

    by_token = await repo.find_by_token("token-abc")
    assert by_token is not None
    assert by_token.object_id == obj_id

    by_object = await repo.find_by_object(obj_id)
    assert len(by_object) == 1
    assert await repo.find_by_token("missing") is None


async def test_share_delete(db_session):
    repo = SqlAlchemyObjectShareRepository(FakeSessionFactory(db_session))
    share_id = IdFactory.generate()
    await repo.save(ObjectShare(
        share_id=share_id, object_id=IdFactory.generate(),
        share_token="t", expires_at=None, created_at=_T0,
    ))
    await db_session.flush()
    await repo.delete(share_id)
    await db_session.flush()
    assert await repo.find_by_id(share_id) is None


# ── reference ─────────────────────────────────────────────────────────────────

async def test_reference_save_find_delete(db_session):
    repo = SqlAlchemyObjectReferenceRepository(FakeSessionFactory(db_session))
    obj_id = IdFactory.generate()
    ref_id = IdFactory.generate()
    await repo.save(ObjectReference(
        reference_id=ref_id,
        object_id=obj_id,
        application_identity_id=IdFactory.generate(),
        application_name="shop",
        resource_type=ResourceType.PRODUCT,
        resource_id="prod-1",
        created_at=_T0,
    ))
    await db_session.flush()

    refs = await repo.find_by_object(obj_id)
    assert len(refs) == 1
    assert refs[0].resource_type == ResourceType.PRODUCT

    await repo.delete(ref_id)
    await db_session.flush()
    assert await repo.find_by_id(ref_id) is None


# ── tag ───────────────────────────────────────────────────────────────────────

async def test_tag_replace_find_delete(db_session):
    repo = SqlAlchemyObjectTagRepository(FakeSessionFactory(db_session))
    obj_id = IdFactory.generate()

    await repo.replace_tags(obj_id, [ObjectTag("a"), ObjectTag("b")])
    await db_session.flush()
    assert {t.value for t in await repo.find_tags(obj_id)} == {"a", "b"}

    # replace overwrites the full set
    await repo.replace_tags(obj_id, [ObjectTag("c")])
    await db_session.flush()
    assert {t.value for t in await repo.find_tags(obj_id)} == {"c"}

    await repo.delete_all(obj_id)
    await db_session.flush()
    assert await repo.find_tags(obj_id) == []
