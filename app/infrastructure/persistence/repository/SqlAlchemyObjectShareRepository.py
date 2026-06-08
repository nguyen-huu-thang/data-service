from sqlalchemy import delete as sql_delete

from xime.starters.sqlalchemy.session import (
    AsyncSessionFactory,
)

from app.domain.object.model.ObjectShare import (
    ObjectShare,
)

from app.infrastructure.persistence.entity.ObjectShareEntity import (
    ObjectShareEntity,
)

from app.infrastructure.persistence.mapper.ObjectShareMapper import (
    ObjectShareMapper,
)


class SqlAlchemyObjectShareRepository:

    def __init__(
        self,
        sessions: AsyncSessionFactory,
    ) -> None:
        self._sessions = sessions

    async def save(
        self,
        share: ObjectShare,
    ) -> None:

        session = self._sessions.current()

        session.add(
            ObjectShareMapper.to_entity(
                share,
            )
        )

    async def find_by_id(
        self,
        share_id: bytes,
    ) -> ObjectShare | None:

        session = self._sessions.current()

        entity = await session.get(
            ObjectShareEntity,
            share_id,
        )

        if entity is None:
            return None

        return ObjectShareMapper.to_model(
            entity,
        )

    async def delete(
        self,
        share_id: bytes,
    ) -> None:

        session = self._sessions.current()

        stmt = sql_delete(
            ObjectShareEntity,
        ).where(
            ObjectShareEntity.share_id
            == share_id,
        )

        await session.execute(
            stmt,
        )