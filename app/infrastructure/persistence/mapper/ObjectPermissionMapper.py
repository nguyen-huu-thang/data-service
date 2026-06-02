from app.common.constants.Role import Role
from app.domain.permission.ObjectPermission import ObjectPermission
from app.infrastructure.persistence.entity.ObjectPermissionEntity import ObjectPermissionEntity


class ObjectPermissionMapper:
    @staticmethod
    def to_domain(entity: ObjectPermissionEntity) -> ObjectPermission:
        return ObjectPermission(
            permission_id=entity.permission_id,
            object_id=entity.object_id,
            subject_identity_id=entity.subject_identity_id,
            role=Role(entity.role),
            created_at=entity.created_at,
        )

    @staticmethod
    def to_entity(domain: ObjectPermission) -> ObjectPermissionEntity:
        return ObjectPermissionEntity(
            permission_id=domain.permission_id,
            object_id=domain.object_id,
            subject_identity_id=domain.subject_identity_id,
            role=domain.role.value,
            created_at=domain.created_at,
        )
