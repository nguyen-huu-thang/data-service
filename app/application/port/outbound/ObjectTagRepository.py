from typing import Protocol

from app.domain.object.valueobject.ObjectTag import (
    ObjectTag,
)


class ObjectTagRepository(Protocol):

    async def replace_tags(
        self,
        object_id: bytes,
        tags: list[ObjectTag],
    ) -> None: ...

    async def find_tags(
        self,
        object_id: bytes,
    ) -> list[ObjectTag]: ...

    async def delete_all(
        self,
        object_id: bytes,
    ) -> None: ...