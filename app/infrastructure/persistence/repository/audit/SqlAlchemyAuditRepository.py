from datetime import datetime, timezone

from xime.starters.sqlalchemy.session import AsyncSessionFactory

from app.common.util.IdGenerator import generate_id
from app.infrastructure.persistence.entity.ObjectAuditEntity import ObjectAuditEntity


class SqlAlchemyAuditRepository:
    def __init__(self, sessions: AsyncSessionFactory) -> None:
        self._sessions = sessions

    async def record(
        self,
        object_id: bytes,
        actor_identity_id: bytes,
        action: str,
    ) -> None:
        session = self._sessions.current()
        entity = ObjectAuditEntity(
            audit_id=generate_id(),
            object_id=object_id,
            actor_identity_id=actor_identity_id,
            action=action,
            created_at=datetime.now(timezone.utc),
        )
        session.add(entity)
