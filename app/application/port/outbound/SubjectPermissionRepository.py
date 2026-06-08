from typing import Protocol

from app.domain.permission.model.SubjectPermission import (
    SubjectPermission,
)


class SubjectPermissionRepository(Protocol):

    async def save(
        self,
        permission: SubjectPermission,
    ) -> None: ...

    async def find_by_id(
        self,
        permission_id: bytes,
    ) -> SubjectPermission | None: ...

    async def delete(
        self,
        permission_id: bytes,
    ) -> None: ...