from sqlalchemy import delete as sql_delete
from sqlalchemy import select

from xime.starters.sqlalchemy.session import AsyncSessionFactory

from app.domain.object.model.ObjectShare import ObjectShare
from app.domain.sharedkernel.model.Id import Id
from app.infrastructure.persistence.entity.ObjectShareEntity import ObjectShareEntity
from app.infrastructure.persistence.mapper.ObjectShareMapper import ObjectShareMapper


class SqlAlchemyObjectShareRepository:

    def __init__(self, sessions: AsyncSessionFactory) -> None:
        self._sessions = sessions

    async def save(self, share: ObjectShare) -> None:
        session = self._sessions.current()
        session.add(ObjectShareMapper.to_entity(share))

    async def find_by_id(self, share_id: Id) -> ObjectShare | None:
        session = self._sessions.current()
        entity = await session.get(ObjectShareEntity, share_id.to_bytes())
        if entity is None:
            return None
        return ObjectShareMapper.to_model(entity)

    async def find_by_token(self, token: str) -> ObjectShare | None:
        session = self._sessions.current()
        stmt = select(ObjectShareEntity).where(ObjectShareEntity.share_token == token)
        entity = (await session.execute(stmt)).scalar_one_or_none()
        if entity is None:
            return None
        return ObjectShareMapper.to_model(entity)

    async def find_by_object(self, object_id: Id) -> list[ObjectShare]:
        session = self._sessions.current()
        stmt = (
            select(ObjectShareEntity)
            .where(ObjectShareEntity.object_id == object_id.to_bytes())
            .order_by(ObjectShareEntity.created_at)
        )
        result = await session.execute(stmt)
        return [ObjectShareMapper.to_model(e) for e in result.scalars().all()]

    async def delete(self, share_id: Id) -> None:
        session = self._sessions.current()
        stmt = sql_delete(ObjectShareEntity).where(
            ObjectShareEntity.share_id == share_id.to_bytes()
        )
        await session.execute(stmt)
