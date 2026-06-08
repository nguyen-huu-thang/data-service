from typing import Protocol

from app.domain.object.model.ObjectReference import (
    ObjectReference,
)


class ObjectReferenceRepository(Protocol):

    async def save(
        self,
        reference: ObjectReference,
    ) -> None: ...

    async def find_by_id(
        self,
        reference_id: bytes,
    ) -> ObjectReference | None: ...

    async def delete(
        self,
        reference_id: bytes,
    ) -> None: ...