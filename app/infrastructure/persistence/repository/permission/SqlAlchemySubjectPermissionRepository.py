from sqlalchemy import delete as sql_delete, select

from xime.starters.sqlalchemy.session import (
    AsyncSessionFactory,
)

from app.domain.permission.model.SubjectPermission import (
    SubjectPermission,
)
from app.domain.sharedkernel.model.Id import Id

from app.infrastructure.persistence.entity.SubjectPermissionEntity import (
    SubjectPermissionEntity,
)

from app.infrastructure.persistence.mapper.SubjectPermissionMapper import (
    SubjectPermissionMapper,
)


class SqlAlchemySubjectPermissionRepository:

    def __init__(
        self,
        sessions: AsyncSessionFactory,
    ) -> None:
        self._sessions = sessions

    async def save(
        self,
        subject_permission: SubjectPermission,
    ) -> None:

        session = self._sessions.current()

        session.add(
            SubjectPermissionMapper.to_entity(
                subject_permission,
            )
        )

    async def find_by_id(
        self,
        permission_id: Id,
    ) -> SubjectPermission | None:

        session = self._sessions.current()

        entity = await session.get(
            SubjectPermissionEntity,
            permission_id.to_bytes(),
        )

        if entity is None:
            return None

        return SubjectPermissionMapper.to_model(
            entity,
        )

    async def find_by_subject(
        self,
        subject_identity_id: Id,
    ) -> list[SubjectPermission]:

        session = self._sessions.current()

        stmt = select(SubjectPermissionEntity).where(
            SubjectPermissionEntity.subject_identity_id == subject_identity_id.to_bytes(),
        )

        result = await session.execute(stmt)

        return [
            SubjectPermissionMapper.to_model(e)
            for e in result.scalars().all()
        ]

    async def delete(
        self,
        permission_id: Id,
    ) -> None:

        session = self._sessions.current()

        stmt = sql_delete(
            SubjectPermissionEntity,
        ).where(
            SubjectPermissionEntity.permission_id
            == permission_id.to_bytes(),
        )

        await session.execute(
            stmt,
        )