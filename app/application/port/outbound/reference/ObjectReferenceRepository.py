from typing import Protocol

from app.domain.object.model.ObjectReference import ObjectReference
from app.domain.sharedkernel.model.Id import Id


class ObjectReferenceRepository(Protocol):

    async def save(self, reference: ObjectReference) -> None: ...

    async def find_by_id(self, reference_id: Id) -> ObjectReference | None: ...

    async def find_by_object(self, object_id: Id) -> list[ObjectReference]: ...

    async def delete(self, reference_id: Id) -> None: ...
