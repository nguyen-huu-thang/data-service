from typing import Protocol

from app.domain.object.model.ObjectShare import ObjectShare
from app.domain.sharedkernel.model.Id import Id


class ObjectShareRepository(Protocol):

    async def save(self, share: ObjectShare) -> None: ...

    async def find_by_id(self, share_id: Id) -> ObjectShare | None: ...

    async def find_by_token(self, token: str) -> ObjectShare | None: ...

    async def find_by_object(self, object_id: Id) -> list[ObjectShare]: ...

    async def delete(self, share_id: Id) -> None: ...
