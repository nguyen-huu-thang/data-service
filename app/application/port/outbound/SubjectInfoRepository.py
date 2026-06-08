from typing import Protocol

from app.domain.subject.model.SubjectInfo import (
    SubjectInfo,
)


class SubjectInfoRepository(Protocol):

    async def save(
        self,
        subject: SubjectInfo,
    ) -> None: ...

    async def find_by_id(
        self,
        identity_id: bytes,
    ) -> SubjectInfo | None: ...

    async def delete(
        self,
        identity_id: bytes,
    ) -> None: ...