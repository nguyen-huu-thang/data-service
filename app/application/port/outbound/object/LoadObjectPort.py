from typing import Protocol

from app.domain.object.model.DataObject import DataObject


class LoadObjectPort(Protocol):
    async def find_by_id(self, object_id: bytes) -> DataObject | None: ...

    async def find_by_owner(
        self,
        owner_identity_id: bytes,
        tenant_id: str | None = None,
    ) -> list[DataObject]: ...

    async def exists(self, object_id: bytes) -> bool: ...
