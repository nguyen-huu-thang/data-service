from typing import Protocol

from app.domain.audit.model.ObjectAudit import ObjectAudit
from app.domain.sharedkernel.model.Id import Id


class LoadAuditPort(Protocol):
    async def find_by_object(self, object_id: Id) -> list[ObjectAudit]: ...
