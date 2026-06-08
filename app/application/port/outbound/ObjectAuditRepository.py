from typing import Protocol

from app.domain.audit.model.ObjectAudit import (
    ObjectAudit,
)


class ObjectAuditRepository(Protocol):

    async def save(
        self,
        audit: ObjectAudit,
    ) -> None: ...

    async def find_by_id(
        self,
        audit_id: bytes,
    ) -> ObjectAudit | None: ...

    async def delete(
        self,
        audit_id: bytes,
    ) -> None: ...