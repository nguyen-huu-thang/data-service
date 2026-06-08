from typing import Protocol

from app.domain.permission.model.ObjectPermission import ObjectPermission


class LoadPermissionPort(Protocol):
    async def find_by_object(self, object_id: bytes) -> list[ObjectPermission]: ...

    async def find_by_subject_and_object(
        self,
        subject_identity_id: bytes,
        object_id: bytes,
    ) -> ObjectPermission | None: ...
