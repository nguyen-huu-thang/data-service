from app.domain.audit.model.ObjectAudit import (
    ObjectAudit,
)
from app.domain.audit.valueobject.AuditAction import (
    AuditAction,
)
from app.domain.sharedkernel.model.Id import Id

from app.infrastructure.persistence.entity.ObjectAuditEntity import (
    ObjectAuditEntity,
)


class ObjectAuditMapper:

    # =========================
    # Entity -> Model
    # =========================

    @staticmethod
    def to_model(
        entity: ObjectAuditEntity,
    ) -> ObjectAudit:

        if entity is None:
            raise ValueError(
                "ObjectAuditEntity must not be null"
            )

        ObjectAuditMapper._require_non_null(
            entity.audit_id,
            "audit_id",
        )

        # object_id is nullable (subject-level actions) — no non-null check.
        # object_id cho phép null (hành động cấp-subject) — không kiểm tra non-null.

        ObjectAuditMapper._require_non_null(
            entity.actor_identity_id,
            "actor_identity_id",
        )

        ObjectAuditMapper._require_non_null(
            entity.actor_subject_type,
            "actor_subject_type",
        )

        ObjectAuditMapper._require_non_null(
            entity.actor_name,
            "actor_name",
        )

        ObjectAuditMapper._require_non_null(
            entity.action,
            "action",
        )

        ObjectAuditMapper._require_non_null(
            entity.created_at,
            "created_at",
        )

        return ObjectAudit(
            audit_id=Id(entity.audit_id),
            object_id=Id(entity.object_id) if entity.object_id is not None else None,
            actor_identity_id=Id(entity.actor_identity_id),
            actor_subject_type=entity.actor_subject_type,
            actor_name=entity.actor_name,
            action=AuditAction(
                entity.action,
            ),
            created_at=entity.created_at,
        )

    # =========================
    # Model -> Entity
    # =========================

    @staticmethod
    def to_entity(
        model: ObjectAudit,
    ) -> ObjectAuditEntity:

        if model is None:
            raise ValueError(
                "ObjectAudit must not be null"
            )

        entity = ObjectAuditEntity()

        entity.audit_id = (
            model.audit_id.to_bytes()
        )

        entity.object_id = (
            model.object_id.to_bytes()
            if model.object_id is not None
            else None
        )

        entity.actor_identity_id = (
            model.actor_identity_id.to_bytes()
        )

        entity.actor_subject_type = (
            model.actor_subject_type
        )

        entity.actor_name = (
            model.actor_name
        )

        entity.action = (
            model.action.value
        )

        entity.created_at = (
            model.created_at
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