from sqlalchemy import delete as sql_delete

from xime.starters.sqlalchemy.session import (
    AsyncSessionFactory,
)

from app.domain.audit.model.ObjectAudit import (
    ObjectAudit,
)

from app.infrastructure.persistence.entity.ObjectAuditEntity import (
    ObjectAuditEntity,
)

from app.infrastructure.persistence.mapper.ObjectAuditMapper import (
    ObjectAuditMapper,
)


class SqlAlchemyObjectAuditRepository:

    def __init__(
        self,
        sessions: AsyncSessionFactory,
    ) -> None:
        self._sessions = sessions

    async def save(
        self,
        object_audit: ObjectAudit,
    ) -> None:

        session = self._sessions.current()

        session.add(
            ObjectAuditMapper.to_entity(
                object_audit,
            )
        )

    async def find_by_id(
        self,
        audit_id: bytes,
    ) -> ObjectAudit | None:

        session = self._sessions.current()

        entity = await session.get(
            ObjectAuditEntity,
            audit_id,
        )

        if entity is None:
            return None

        return ObjectAuditMapper.to_model(
            entity,
        )

    async def delete(
        self,
        audit_id: bytes,
    ) -> None:

        session = self._sessions.current()

        stmt = sql_delete(
            ObjectAuditEntity,
        ).where(
            ObjectAuditEntity.audit_id
            == audit_id,
        )

        await session.execute(
            stmt,
        )