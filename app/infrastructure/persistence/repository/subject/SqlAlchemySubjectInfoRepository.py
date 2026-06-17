from sqlalchemy import delete as sql_delete

from xime.starters.sqlalchemy.session import (
    AsyncSessionFactory,
)

from app.domain.subject.model.SubjectInfo import (
    SubjectInfo,
)
from app.domain.sharedkernel.model.Id import Id

from app.infrastructure.persistence.entity.SubjectInfoEntity import (
    SubjectInfoEntity,
)

from app.infrastructure.persistence.mapper.SubjectInfoMapper import (
    SubjectInfoMapper,
)


class SqlAlchemySubjectInfoRepository:

    def __init__(
        self,
        sessions: AsyncSessionFactory,
    ) -> None:
        self._sessions = sessions

    async def save(
        self,
        subject_info: SubjectInfo,
    ) -> None:

        session = self._sessions.current()

        session.add(
            SubjectInfoMapper.to_entity(
                subject_info,
            )
        )

    async def find_by_id(
        self,
        identity_id: Id,
    ) -> SubjectInfo | None:

        session = self._sessions.current()

        entity = await session.get(
            SubjectInfoEntity,
            identity_id.to_bytes(),
        )

        if entity is None:
            return None

        return SubjectInfoMapper.to_model(
            entity,
        )

    async def delete(
        self,
        identity_id: Id,
    ) -> None:

        session = self._sessions.current()

        stmt = sql_delete(
            SubjectInfoEntity,
        ).where(
            SubjectInfoEntity.identity_id
            == identity_id.to_bytes(),
        )

        await session.execute(
            stmt,
        )