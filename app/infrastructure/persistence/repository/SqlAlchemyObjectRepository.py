from sqlalchemy import delete as sql_delete

from xime.starters.sqlalchemy.session import (
    AsyncSessionFactory,
)

from app.domain.object.model.DataObject import (
    DataObject,
)

from app.infrastructure.persistence.entity.DataObjectEntity import (
    DataObjectEntity,
)

from app.infrastructure.persistence.mapper.DataObjectMapper import (
    DataObjectMapper,
)


class SqlAlchemyObjectRepository:

    def __init__(
        self,
        sessions: AsyncSessionFactory,
    ) -> None:
        self._sessions = sessions

    async def save(
        self,
        data_object: DataObject,
    ) -> None:

        session = self._sessions.current()

        session.add(
            DataObjectMapper.to_entity(
                data_object,
            )
        )

    async def find_by_id(
        self,
        object_id: bytes,
    ) -> DataObject | None:

        session = self._sessions.current()

        entity = await session.get(
            DataObjectEntity,
            object_id,
        )

        if entity is None:
            return None

        return DataObjectMapper.to_domain(
            entity,
        )

    async def delete(
        self,
        object_id: bytes,
    ) -> None:

        session = self._sessions.current()

        stmt = sql_delete(
            DataObjectEntity,
        ).where(
            DataObjectEntity.object_id
            == object_id,
        )

        await session.execute(
            stmt,
        )