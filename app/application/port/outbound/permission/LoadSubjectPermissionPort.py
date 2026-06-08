from typing import Protocol

from app.domain.permission.model.SubjectPermission import SubjectPermission


class LoadSubjectPermissionPort(Protocol):
    async def find_by_subject(
        self,
        subject_identity_id: bytes,
    ) -> list[SubjectPermission]: ...
