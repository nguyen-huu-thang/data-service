from typing import Protocol

from app.domain.object.model.ObjectVersion import (
    ObjectVersion,
)


class ObjectVersionRepository(Protocol):

    async def save(
        self,
        version: ObjectVersion,
    ) -> None: ...

    async def find_by_id(
        self,
        version_id: bytes,
    ) -> ObjectVersion | None: ...

    async def delete(
        self,
        version_id: bytes,
    ) -> None: ...