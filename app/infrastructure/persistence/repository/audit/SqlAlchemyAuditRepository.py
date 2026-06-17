from sqlalchemy import select

from xime.starters.sqlalchemy.session import AsyncSessionFactory

from app.domain.audit.model.ObjectAudit import ObjectAudit
from app.domain.sharedkernel.model.Id import Id
from app.infrastructure.persistence.entity.ObjectAuditEntity import ObjectAuditEntity
from app.infrastructure.persistence.mapper.ObjectAuditMapper import ObjectAuditMapper


class SqlAlchemyAuditRepository:
    """
    Unified audit repository: persists and reads `ObjectAudit` via the domain
    model + `ObjectAuditMapper` (no raw-field writes).

    Repo audit hợp nhất: ghi/đọc `ObjectAudit` qua domain model + mapper
    (không ghi trường thô).
    """

    def __init__(self, sessions: AsyncSessionFactory) -> None:
        self._sessions = sessions

    async def save(self, audit: ObjectAudit) -> None:
        session = self._sessions.current()
        session.add(ObjectAuditMapper.to_entity(audit))

    async def find_by_object(self, object_id: Id) -> list[ObjectAudit]:
        session = self._sessions.current()
        stmt = (
            select(ObjectAuditEntity)
            .where(ObjectAuditEntity.object_id == object_id.to_bytes())
            .order_by(ObjectAuditEntity.created_at)
        )
        result = await session.execute(stmt)
        return [ObjectAuditMapper.to_model(e) for e in result.scalars().all()]
