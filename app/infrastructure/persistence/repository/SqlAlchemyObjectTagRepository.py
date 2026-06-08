from sqlalchemy import delete as sql_delete
from sqlalchemy import select

from xime.starters.sqlalchemy.session import (
    AsyncSessionFactory,
)

from app.domain.object.valueobject.ObjectTag import (
    ObjectTag,
)

from app.infrastructure.persistence.entity.ObjectTagEntity import (
    ObjectTagEntity,
)


class SqlAlchemyObjectTagRepository:

    def __init__(
        self,
        sessions: AsyncSessionFactory,
    ) -> None:
        self._sessions = sessions

    async def replace_tags(
        self,
        object_id: bytes,
        tags: list[ObjectTag],
    ) -> None:

        session = self._sessions.current()

        stmt = sql_delete(
            ObjectTagEntity,
        ).where(
            ObjectTagEntity.object_id
            == object_id,
        )

        await session.execute(
            stmt,
        )

        for tag in tags:
            session.add(
                ObjectTagEntity(
                    object_id=object_id,
                    tag=tag.value,
                )
            )

    async def find_tags(
        self,
        object_id: bytes,
    ) -> list[ObjectTag]:

        session = self._sessions.current()

        stmt = select(
            ObjectTagEntity,
        ).where(
            ObjectTagEntity.object_id
            == object_id,
        )

        result = await session.execute(
            stmt,
        )

        entities = (
            result.scalars().all()
        )

        return [
            ObjectTag(
                entity.tag,
            )
            for entity in entities
        ]

    async def delete_all(
        self,
        object_id: bytes,
    ) -> None:

        session = self._sessions.current()

        stmt = sql_delete(
            ObjectTagEntity,
        ).where(
            ObjectTagEntity.object_id
            == object_id,
        )

        await session.execute(
            stmt,
        )