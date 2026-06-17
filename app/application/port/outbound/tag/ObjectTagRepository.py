from typing import Protocol

from app.domain.object.valueobject.ObjectTag import ObjectTag
from app.domain.sharedkernel.model.Id import Id


class ObjectTagRepository(Protocol):

    async def replace_tags(self, object_id: Id, tags: list[ObjectTag]) -> None: ...

    async def find_tags(self, object_id: Id) -> list[ObjectTag]: ...

    async def delete_all(self, object_id: Id) -> None: ...
