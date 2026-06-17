from typing import Protocol

from app.domain.permission.model.ObjectPermission import ObjectPermission
from app.domain.sharedkernel.model.Id import Id


class SavePermissionPort(Protocol):
    async def save(self, permission: ObjectPermission) -> None: ...

    async def delete(self, permission_id: Id) -> None: ...

    async def delete_all_by_object(self, object_id: Id) -> None: ...
