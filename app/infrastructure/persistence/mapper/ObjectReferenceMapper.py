from app.domain.object.model.ObjectReference import (
    ObjectReference,
)
from app.domain.object.valueobject.ResourceType import (
    ResourceType,
)

from app.infrastructure.persistence.entity.ObjectReferenceEntity import (
    ObjectReferenceEntity,
)


class ObjectReferenceMapper:

    # =========================
    # Entity -> Model
    # =========================

    @staticmethod
    def to_model(
        entity: ObjectReferenceEntity,
    ) -> ObjectReference:

        if entity is None:
            raise ValueError(
                "ObjectReferenceEntity must not be null"
            )

        ObjectReferenceMapper._require_non_null(
            entity.reference_id,
            "reference_id",
        )

        ObjectReferenceMapper._require_non_null(
            entity.object_id,
            "object_id",
        )

        ObjectReferenceMapper._require_non_null(
            entity.application_identity_id,
            "application_identity_id",
        )

        ObjectReferenceMapper._require_non_null(
            entity.application_name,
            "application_name",
        )

        ObjectReferenceMapper._require_non_null(
            entity.resource_type,
            "resource_type",
        )

        ObjectReferenceMapper._require_non_null(
            entity.resource_id,
            "resource_id",
        )

        ObjectReferenceMapper._require_non_null(
            entity.created_at,
            "created_at",
        )

        return ObjectReference(
            reference_id=entity.reference_id,
            object_id=entity.object_id,
            application_identity_id=entity.application_identity_id,
            application_name=entity.application_name,
            resource_type=ResourceType(
                entity.resource_type,
            ),
            resource_id=entity.resource_id,
            created_at=entity.created_at,
        )

    # =========================
    # Model -> Entity
    # =========================

    @staticmethod
    def to_entity(
        model: ObjectReference,
    ) -> ObjectReferenceEntity:

        if model is None:
            raise ValueError(
                "ObjectReference must not be null"
            )

        entity = ObjectReferenceEntity()

        entity.reference_id = model.reference_id

        entity.object_id = model.object_id

        entity.application_identity_id = (
            model.application_identity_id
        )

        entity.application_name = (
            model.application_name
        )

        entity.resource_type = (
            model.resource_type.value
        )

        entity.resource_id = (
            model.resource_id
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