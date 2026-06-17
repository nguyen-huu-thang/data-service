from sqlalchemy import delete as sql_delete
from sqlalchemy import select

from xime.starters.sqlalchemy.session import AsyncSessionFactory

from app.domain.object.model.ObjectReference import ObjectReference
from app.domain.sharedkernel.model.Id import Id
from app.infrastructure.persistence.entity.ObjectReferenceEntity import ObjectReferenceEntity
from app.infrastructure.persistence.mapper.ObjectReferenceMapper import ObjectReferenceMapper


class SqlAlchemyObjectReferenceRepository:

    def __init__(self, sessions: AsyncSessionFactory) -> None:
        self._sessions = sessions

    async def save(self, reference: ObjectReference) -> None:
        session = self._sessions.current()
        session.add(ObjectReferenceMapper.to_entity(reference))

    async def find_by_id(self, reference_id: Id) -> ObjectReference | None:
        session = self._sessions.current()
        entity = await session.get(ObjectReferenceEntity, reference_id.to_bytes())
        if entity is None:
            return None
        return ObjectReferenceMapper.to_model(entity)

    async def find_by_object(self, object_id: Id) -> list[ObjectReference]:
        session = self._sessions.current()
        stmt = (
            select(ObjectReferenceEntity)
            .where(ObjectReferenceEntity.object_id == object_id.to_bytes())
            .order_by(ObjectReferenceEntity.created_at)
        )
        result = await session.execute(stmt)
        return [ObjectReferenceMapper.to_model(e) for e in result.scalars().all()]

    async def delete(self, reference_id: Id) -> None:
        session = self._sessions.current()
        stmt = sql_delete(ObjectReferenceEntity).where(
            ObjectReferenceEntity.reference_id == reference_id.to_bytes()
        )
        await session.execute(stmt)
