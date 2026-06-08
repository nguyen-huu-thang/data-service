from app.domain.permission.model.ObjectPermission import ObjectPermission
from app.domain.permission.role.Role import Role

from app.infrastructure.persistence.entity.ObjectPermissionEntity import ObjectPermissionEntity


class ObjectPermissionMapper:

    # =========================
    # Entity -> Domain Model
    # =========================

    @staticmethod
    def to_domain(entity: ObjectPermissionEntity) -> ObjectPermission:

        if entity is None:
            raise ValueError("ObjectPermissionEntity must not be null")

        ObjectPermissionMapper._require_non_null(entity.permission_id, "permission_id")
        ObjectPermissionMapper._require_non_null(entity.object_id, "object_id")
        ObjectPermissionMapper._require_non_null(entity.subject_identity_id, "subject_identity_id")
        ObjectPermissionMapper._require_non_null(entity.subject_type, "subject_type")
        ObjectPermissionMapper._require_non_null(entity.role, "role")
        ObjectPermissionMapper._require_non_null(entity.created_at, "created_at")

        return ObjectPermission(
            permission_id=entity.permission_id,
            object_id=entity.object_id,
            subject_identity_id=entity.subject_identity_id,
            subject_type=entity.subject_type,
            role=Role(entity.role),
            created_at=entity.created_at,
        )

    # =========================
    # Domain Model -> Entity
    # =========================

    @staticmethod
    def to_entity(model: ObjectPermission) -> ObjectPermissionEntity:

        if model is None:
            raise ValueError("ObjectPermission must not be null")

        entity = ObjectPermissionEntity()

        entity.permission_id = model.permission_id
        entity.object_id = model.object_id
        entity.subject_identity_id = model.subject_identity_id
        entity.subject_type = model.subject_type
        entity.role = model.role.value
        entity.created_at = model.created_at

        return entity

    # =========================
    # Helpers
    # =========================

    @staticmethod
    def _require_non_null(value: object, field: str) -> None:
        if value is None:
            raise ValueError(f"{field} must not be null")
