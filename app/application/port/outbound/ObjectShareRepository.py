from typing import Protocol

from app.domain.object.model.ObjectShare import (
    ObjectShare,
)


class ObjectShareRepository(Protocol):

    async def save(
        self,
        share: ObjectShare,
    ) -> None: ...

    async def find_by_id(
        self,
        share_id: bytes,
    ) -> ObjectShare | None: ...

    async def delete(
        self,
        share_id: bytes,
    ) -> None: ...