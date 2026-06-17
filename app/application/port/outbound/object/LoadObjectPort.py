from typing import Protocol

from app.domain.object.model.DataObject import DataObject
from app.domain.sharedkernel.model.Id import Id


class LoadObjectPort(Protocol):
    async def find_by_id(self, object_id: Id) -> DataObject | None: ...

    async def find_by_id_for_update(self, object_id: Id) -> DataObject | None:
        """Load the object while taking a row-level lock (SELECT ... FOR UPDATE).

        Must be called inside an active transaction. Serializes concurrent
        writers on the same object (e.g. version creation, purge) so they
        cannot race on derived state.
        """
        ...

    async def find_by_owner(
        self,
        owner_identity_id: Id,
        tenant_id: str | None = None,
    ) -> list[DataObject]: ...

    async def exists(self, object_id: Id) -> bool: ...
