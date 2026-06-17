from typing import Protocol

from app.domain.audit.model.ObjectAudit import ObjectAudit


class SaveAuditPort(Protocol):
    async def save(self, audit: ObjectAudit) -> None: ...
