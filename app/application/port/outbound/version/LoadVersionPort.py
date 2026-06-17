from typing import Protocol

from app.domain.object.model.ObjectVersion import ObjectVersion
from app.domain.sharedkernel.model.Id import Id


class LoadVersionPort(Protocol):
    async def find_by_id(self, version_id: Id) -> ObjectVersion | None: ...

    async def find_by_object(self, object_id: Id) -> list[ObjectVersion]: ...

    async def find_latest_by_object(self, object_id: Id) -> ObjectVersion | None: ...

    async def count_by_object(self, object_id: Id) -> int: ...
