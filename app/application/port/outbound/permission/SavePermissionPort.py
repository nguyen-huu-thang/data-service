from typing import Protocol

from app.domain.permission.ObjectPermission import ObjectPermission


class SavePermissionPort(Protocol):
    async def save(self, permission: ObjectPermission) -> None: ...

    async def delete(self, permission_id: bytes) -> None: ...

    async def delete_all_by_object(self, object_id: bytes) -> None: ...
