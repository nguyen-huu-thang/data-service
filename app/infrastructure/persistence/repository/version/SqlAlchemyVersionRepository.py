from sqlalchemy import func, select
from starters.sqlalchemy.session import AsyncSessionFactory

from app.domain.object.ObjectVersion import ObjectVersion
from app.infrastructure.persistence.entity.ObjectVersionEntity import ObjectVersionEntity
from app.infrastructure.persistence.mapper.ObjectVersionMapper import ObjectVersionMapper


class SqlAlchemyVersionRepository:
    def __init__(self, sessions: AsyncSessionFactory) -> None:
        self._sessions = sessions

    async def find_by_id(self, version_id: bytes) -> ObjectVersion | None:
        session = self._sessions.current()
        entity = await session.get(ObjectVersionEntity, version_id)
        return ObjectVersionMapper.to_domain(entity) if entity else None

    async def find_by_object(self, object_id: bytes) -> list[ObjectVersion]:
        session = self._sessions.current()
        stmt = (
            select(ObjectVersionEntity)
            .where(ObjectVersionEntity.object_id == object_id)
            .order_by(ObjectVersionEntity.version_number)
        )
        result = await session.execute(stmt)
        return [ObjectVersionMapper.to_domain(e) for e in result.scalars().all()]

    async def find_latest_by_object(self, object_id: bytes) -> ObjectVersion | None:
        session = self._sessions.current()
        stmt = (
            select(ObjectVersionEntity)
            .where(ObjectVersionEntity.object_id == object_id)
            .order_by(ObjectVersionEntity.version_number.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        entity = result.scalar_one_or_none()
        return ObjectVersionMapper.to_domain(entity) if entity else None

    async def count_by_object(self, object_id: bytes) -> int:
        session = self._sessions.current()
        stmt = (
            select(func.count())
            .select_from(ObjectVersionEntity)
            .where(ObjectVersionEntity.object_id == object_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one()

    async def save(self, version: ObjectVersion) -> None:
        session = self._sessions.current()
        session.add(ObjectVersionMapper.to_entity(version))
