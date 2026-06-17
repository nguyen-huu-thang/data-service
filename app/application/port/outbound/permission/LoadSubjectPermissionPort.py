from typing import Protocol

from app.domain.permission.model.SubjectPermission import SubjectPermission
from app.domain.sharedkernel.model.Id import Id


class LoadSubjectPermissionPort(Protocol):
    async def find_by_subject(
        self,
        subject_identity_id: Id,
    ) -> list[SubjectPermission]: ...
