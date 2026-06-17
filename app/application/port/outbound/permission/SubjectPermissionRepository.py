from typing import Protocol

from app.domain.permission.model.SubjectPermission import (
    SubjectPermission,
)
from app.domain.sharedkernel.model.Id import Id


class SubjectPermissionRepository(Protocol):

    async def save(
        self,
        permission: SubjectPermission,
    ) -> None: ...

    async def find_by_id(
        self,
        permission_id: Id,
    ) -> SubjectPermission | None: ...

    async def delete(
        self,
        permission_id: Id,
    ) -> None: ...