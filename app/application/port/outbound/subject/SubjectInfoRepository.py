from typing import Protocol

from app.domain.subject.model.SubjectInfo import (
    SubjectInfo,
)
from app.domain.sharedkernel.model.Id import Id


class SubjectInfoRepository(Protocol):

    async def save(
        self,
        subject: SubjectInfo,
    ) -> None: ...

    async def find_by_id(
        self,
        identity_id: Id,
    ) -> SubjectInfo | None: ...

    async def delete(
        self,
        identity_id: Id,
    ) -> None: ...