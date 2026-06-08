from sqlalchemy import delete as sql_delete, select
from xime.starters.sqlalchemy.session import AsyncSessionFactory

from app.domain.permission.model.ObjectPermission import ObjectPermission
from app.infrastructure.persistence.entity.ObjectPermissionEntity import ObjectPermissionEntity
from app.infrastructure.persistence.mapper.ObjectPermissionMapper import ObjectPermissionMapper


class SqlAlchemyPermissionRepository:
    def __init__(self, sessions: AsyncSessionFactory) -> None:
        self._sessions = sessions

    async def find_by_object(self, object_id: bytes) -> list[ObjectPermission]:
        session = self._sessions.current()
        stmt = select(ObjectPermissionEntity).where(
            ObjectPermissionEntity.object_id == object_id
        )
        result = await session.execute(stmt)
        return [ObjectPermissionMapper.to_domain(e) for e in result.scalars().all()]

    async def find_by_subject_and_object(
        self,
        subject_identity_id: bytes,
        object_id: bytes,
    ) -> ObjectPermission | None:
        session = self._sessions.current()
        stmt = select(ObjectPermissionEntity).where(
            ObjectPermissionEntity.subject_identity_id == subject_identity_id,
            ObjectPermissionEntity.object_id == object_id,
        )
        result = await session.execute(stmt)
        entity = result.scalar_one_or_none()
        return ObjectPermissionMapper.to_domain(entity) if entity else None

    async def save(self, permission: ObjectPermission) -> None:
        session = self._sessions.current()
        session.add(ObjectPermissionMapper.to_entity(permission))

    async def delete(self, permission_id: bytes) -> None:
        session = self._sessions.current()
        stmt = sql_delete(ObjectPermissionEntity).where(
            ObjectPermissionEntity.permission_id == permission_id
        )
        await session.execute(stmt)

    async def delete_all_by_object(self, object_id: bytes) -> None:
        session = self._sessions.current()
        stmt = sql_delete(ObjectPermissionEntity).where(
            ObjectPermissionEntity.object_id == object_id
        )
        await session.execute(stmt)
