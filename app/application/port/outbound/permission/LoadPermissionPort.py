from typing import Protocol

from app.domain.permission.model.ObjectPermission import ObjectPermission
from app.domain.sharedkernel.model.Id import Id


class LoadPermissionPort(Protocol):
    async def find_by_object(self, object_id: Id) -> list[ObjectPermission]: ...

    async def find_by_subject_and_object(
        self,
        subject_identity_id: Id,
        object_id: Id,
    ) -> ObjectPermission | None: ...
