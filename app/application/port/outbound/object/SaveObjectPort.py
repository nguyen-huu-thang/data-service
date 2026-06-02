from typing import Protocol

from app.domain.object.DataObject import DataObject


class SaveObjectPort(Protocol):
    async def save(self, obj: DataObject) -> None: ...

    async def update(self, obj: DataObject) -> None: ...
