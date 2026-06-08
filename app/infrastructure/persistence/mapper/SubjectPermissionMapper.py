from app.domain.permission.capability.ObjectCapability import (
    ObjectCapability,
)
from app.domain.permission.model.SubjectPermission import (
    SubjectPermission,
)
from app.domain.subject.valueobject.SubjectType import (
    SubjectType,
)

from app.infrastructure.persistence.entity.SubjectPermissionEntity import (
    SubjectPermissionEntity,
)


class SubjectPermissionMapper:

    # =========================
    # Entity -> Model
    # =========================

    @staticmethod
    def to_model(
        entity: SubjectPermissionEntity,
    ) -> SubjectPermission:

        if entity is None:
            raise ValueError(
                "SubjectPermissionEntity must not be null"
            )

        SubjectPermissionMapper._require_non_null(
            entity.permission_id,
            "permission_id",
        )

        SubjectPermissionMapper._require_non_null(
            entity.subject_identity_id,
            "subject_identity_id",
        )

        SubjectPermissionMapper._require_non_null(
            entity.subject_type,
            "subject_type",
        )

        SubjectPermissionMapper._require_non_null(
            entity.permission,
            "permission",
        )

        SubjectPermissionMapper._require_non_null(
            entity.created_at,
            "created_at",
        )

        SubjectPermissionMapper._require_non_null(
            entity.updated_at,
            "updated_at",
        )

        return SubjectPermission(
            permission_id=entity.permission_id,
            subject_identity_id=entity.subject_identity_id,
            subject_type=SubjectType(
                entity.subject_type,
            ),
            permission=ObjectCapability(
                entity.permission,
            ),
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    # =========================
    # Model -> Entity
    # =========================

    @staticmethod
    def to_entity(
        model: SubjectPermission,
    ) -> SubjectPermissionEntity:

        if model is None:
            raise ValueError(
                "SubjectPermission must not be null"
            )

        entity = SubjectPermissionEntity()

        entity.permission_id = (
            model.permission_id
        )

        entity.subject_identity_id = (
            model.subject_identity_id
        )

        entity.subject_type = (
            model.subject_type.value
        )

        entity.permission = (
            model.permission.value
        )

        entity.created_at = (
            model.created_at
        )

        entity.updated_at = (
            model.updated_at
        )

        return entity

    # =========================
    # Helpers
    # =========================

    @staticmethod
    def _require_non_null(
        value: object,
        field: str,
    ) -> None:

        if value is None:
            raise ValueError(
                f"{field} must not be null"
            )