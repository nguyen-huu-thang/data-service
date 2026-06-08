from typing import Protocol

from app.domain.permission.model.ObjectPermission import (
    ObjectPermission,
)


class ObjectPermissionRepository(Protocol):

    async def save(
        self,
        permission: ObjectPermission,
    ) -> None: ...

    async def find_by_id(
        self,
        permission_id: bytes,
    ) -> ObjectPermission | None: ...

    async def delete(
        self,
        permission_id: bytes,
    ) -> None: ...