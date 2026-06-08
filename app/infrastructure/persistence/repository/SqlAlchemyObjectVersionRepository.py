from sqlalchemy import delete as sql_delete

from xime.starters.sqlalchemy.session import (
    AsyncSessionFactory,
)

from app.domain.object.model.ObjectVersion import (
    ObjectVersion,
)

from app.infrastructure.persistence.entity.ObjectVersionEntity import (
    ObjectVersionEntity,
)

from app.infrastructure.persistence.mapper.ObjectVersionMapper import (
    ObjectVersionMapper,
)


class SqlAlchemyObjectVersionRepository:

    def __init__(
        self,
        sessions: AsyncSessionFactory,
    ) -> None:
        self._sessions = sessions

    async def save(
        self,
        version: ObjectVersion,
    ) -> None:

        session = self._sessions.current()

        session.add(
            ObjectVersionMapper.to_entity(
                version,
            )
        )

    async def find_by_id(
        self,
        version_id: bytes,
    ) -> ObjectVersion | None:

        session = self._sessions.current()

        entity = await session.get(
            ObjectVersionEntity,
            version_id,
        )

        if entity is None:
            return None

        return ObjectVersionMapper.to_domain(
            entity,
        )

    async def delete(
        self,
        version_id: bytes,
    ) -> None:

        session = self._sessions.current()

        stmt = sql_delete(
            ObjectVersionEntity,
        ).where(
            ObjectVersionEntity.version_id
            == version_id,
        )

        await session.execute(
            stmt,
        )