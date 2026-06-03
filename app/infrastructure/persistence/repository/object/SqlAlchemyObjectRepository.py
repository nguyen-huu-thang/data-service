from sqlalchemy import select
from xime.starters.sqlalchemy.session import AsyncSessionFactory

from app.domain.object.DataObject import DataObject
from app.infrastructure.persistence.entity.DataObjectEntity import DataObjectEntity
from app.infrastructure.persistence.mapper.DataObjectMapper import DataObjectMapper


class SqlAlchemyObjectRepository:
    def __init__(self, sessions: AsyncSessionFactory) -> None:
        self._sessions = sessions

    async def find_by_id(self, object_id: bytes) -> DataObject | None:
        session = self._sessions.current()
        entity = await session.get(DataObjectEntity, object_id)
        return DataObjectMapper.to_domain(entity) if entity else None

    async def find_by_owner(
        self,
        owner_identity_id: bytes,
        tenant_id: str | None = None,
    ) -> list[DataObject]:
        session = self._sessions.current()
        stmt = select(DataObjectEntity).where(
            DataObjectEntity.owner_identity_id == owner_identity_id
        )
        if tenant_id is not None:
            stmt = stmt.where(DataObjectEntity.tenant_id == tenant_id)
        result = await session.execute(stmt)
        return [DataObjectMapper.to_domain(e) for e in result.scalars().all()]

    async def exists(self, object_id: bytes) -> bool:
        session = self._sessions.current()
        entity = await session.get(DataObjectEntity, object_id)
        return entity is not None

    async def save(self, obj: DataObject) -> None:
        session = self._sessions.current()
        session.add(DataObjectMapper.to_entity(obj))

    async def update(self, obj: DataObject) -> None:
        session = self._sessions.current()
        await session.merge(DataObjectMapper.to_entity(obj))
