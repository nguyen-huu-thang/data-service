from typing import Protocol

from app.domain.object.model.DataObject import DataObject


class ObjectRepository(Protocol):

    async def save(
        self,
        data_object: DataObject,
    ) -> None: ...

    async def find_by_id(
        self,
        object_id: bytes,
    ) -> DataObject | None: ...

    async def delete(
        self,
        object_id: bytes,
    ) -> None: ...