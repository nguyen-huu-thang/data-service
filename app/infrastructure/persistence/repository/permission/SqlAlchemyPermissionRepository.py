from sqlalchemy import delete as sql_delete, select
from xime.starters.sqlalchemy.session import AsyncSessionFactory

from app.domain.permission.model.ObjectPermission import ObjectPermission
from app.domain.sharedkernel.model.Id import Id
from app.infrastructure.persistence.entity.ObjectPermissionEntity import ObjectPermissionEntity
from app.infrastructure.persistence.mapper.ObjectPermissionMapper import ObjectPermissionMapper


class SqlAlchemyPermissionRepository:
    def __init__(self, sessions: AsyncSessionFactory) -> None:
        self._sessions = sessions

    async def find_by_object(self, object_id: Id) -> list[ObjectPermission]:
        session = self._sessions.current()
        stmt = select(ObjectPermissionEntity).where(
            ObjectPermissionEntity.object_id == object_id.to_bytes()
        )
        result = await session.execute(stmt)
        return [ObjectPermissionMapper.to_domain(e) for e in result.scalars().all()]

    async def find_by_subject_and_object(
        self,
        subject_identity_id: Id,
        object_id: Id,
    ) -> ObjectPermission | None:
        session = self._sessions.current()
        stmt = select(ObjectPermissionEntity).where(
            ObjectPermissionEntity.subject_identity_id == subject_identity_id.to_bytes(),
            ObjectPermissionEntity.object_id == object_id.to_bytes(),
        )
        result = await session.execute(stmt)
        entity = result.scalar_one_or_none()
        return ObjectPermissionMapper.to_domain(entity) if entity else None

    async def save(self, permission: ObjectPermission) -> None:
        session = self._sessions.current()
        session.add(ObjectPermissionMapper.to_entity(permission))

    async def delete(self, permission_id: Id) -> None:
        session = self._sessions.current()
        stmt = sql_delete(ObjectPermissionEntity).where(
            ObjectPermissionEntity.permission_id == permission_id.to_bytes()
        )
        await session.execute(stmt)

    async def delete_all_by_object(self, object_id: Id) -> None:
        session = self._sessions.current()
        stmt = sql_delete(ObjectPermissionEntity).where(
            ObjectPermissionEntity.object_id == object_id.to_bytes()
        )
        await session.execute(stmt)
