from sqlalchemy import delete as sql_delete

from xime.starters.sqlalchemy.session import (
    AsyncSessionFactory,
)

from app.domain.object.model.ObjectReference import (
    ObjectReference,
)

from app.infrastructure.persistence.entity.ObjectReferenceEntity import (
    ObjectReferenceEntity,
)

from app.infrastructure.persistence.mapper.ObjectReferenceMapper import (
    ObjectReferenceMapper,
)


class SqlAlchemyObjectReferenceRepository:

    def __init__(
        self,
        sessions: AsyncSessionFactory,
    ) -> None:
        self._sessions = sessions

    async def save(
        self,
        reference: ObjectReference,
    ) -> None:

        session = self._sessions.current()

        session.add(
            ObjectReferenceMapper.to_entity(
                reference,
            )
        )

    async def find_by_id(
        self,
        reference_id: bytes,
    ) -> ObjectReference | None:

        session = self._sessions.current()

        entity = await session.get(
            ObjectReferenceEntity,
            reference_id,
        )

        if entity is None:
            return None

        return ObjectReferenceMapper.to_model(
            entity,
        )

    async def delete(
        self,
        reference_id: bytes,
    ) -> None:

        session = self._sessions.current()

        stmt = sql_delete(
            ObjectReferenceEntity,
        ).where(
            ObjectReferenceEntity.reference_id
            == reference_id,
        )

        await session.execute(
            stmt,
        )