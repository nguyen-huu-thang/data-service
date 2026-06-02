from typing import Protocol

from app.domain.object.ObjectVersion import ObjectVersion


class SaveVersionPort(Protocol):
    async def save(self, version: ObjectVersion) -> None: ...
