from app.domain.object.model.ObjectShare import (
    ObjectShare,
)

from app.infrastructure.persistence.entity.ObjectShareEntity import (
    ObjectShareEntity,
)


class ObjectShareMapper:

    # =========================
    # Entity -> Model
    # =========================

    @staticmethod
    def to_model(
        entity: ObjectShareEntity,
    ) -> ObjectShare:

        if entity is None:
            raise ValueError(
                "ObjectShareEntity must not be null"
            )

        ObjectShareMapper._require_non_null(
            entity.share_id,
            "share_id",
        )

        ObjectShareMapper._require_non_null(
            entity.object_id,
            "object_id",
        )

        ObjectShareMapper._require_non_null(
            entity.share_token,
            "share_token",
        )

        ObjectShareMapper._require_non_null(
            entity.created_at,
            "created_at",
        )

        return ObjectShare(
            share_id=entity.share_id,
            object_id=entity.object_id,
            share_token=entity.share_token,
            expires_at=entity.expires_at,
            created_at=entity.created_at,
        )

    # =========================
    # Model -> Entity
    # =========================

    @staticmethod
    def to_entity(
        model: ObjectShare,
    ) -> ObjectShareEntity:

        if model is None:
            raise ValueError(
                "ObjectShare must not be null"
            )

        entity = ObjectShareEntity()

        entity.share_id = model.share_id

        entity.object_id = model.object_id

        entity.share_token = (
            model.share_token
        )

        entity.expires_at = (
            model.expires_at
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