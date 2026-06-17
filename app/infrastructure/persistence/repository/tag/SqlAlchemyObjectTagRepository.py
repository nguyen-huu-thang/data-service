from sqlalchemy import delete as sql_delete
from sqlalchemy import select

from xime.starters.sqlalchemy.session import AsyncSessionFactory

from app.domain.object.valueobject.ObjectTag import ObjectTag
from app.domain.sharedkernel.model.Id import Id
from app.infrastructure.persistence.entity.ObjectTagEntity import ObjectTagEntity


class SqlAlchemyObjectTagRepository:

    def __init__(self, sessions: AsyncSessionFactory) -> None:
        self._sessions = sessions

    async def replace_tags(self, object_id: Id, tags: list[ObjectTag]) -> None:
        session = self._sessions.current()
        await session.execute(
            sql_delete(ObjectTagEntity).where(
                ObjectTagEntity.object_id == object_id.to_bytes()
            )
        )
        for tag in tags:
            session.add(ObjectTagEntity(object_id=object_id.to_bytes(), tag=tag.value))

    async def find_tags(self, object_id: Id) -> list[ObjectTag]:
        session = self._sessions.current()
        stmt = select(ObjectTagEntity).where(
            ObjectTagEntity.object_id == object_id.to_bytes()
        )
        result = await session.execute(stmt)
        return [ObjectTag(e.tag) for e in result.scalars().all()]

    async def delete_all(self, object_id: Id) -> None:
        session = self._sessions.current()
        await session.execute(
            sql_delete(ObjectTagEntity).where(
                ObjectTagEntity.object_id == object_id.to_bytes()
            )
        )
