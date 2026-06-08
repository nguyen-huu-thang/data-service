from app.domain.subject.model.SubjectInfo import (
    SubjectInfo,
)
from app.domain.subject.valueobject.SubjectType import (
    SubjectType,
)

from app.infrastructure.persistence.entity.SubjectInfoEntity import (
    SubjectInfoEntity,
)


class SubjectInfoMapper:

    # =========================
    # Entity -> Model
    # =========================

    @staticmethod
    def to_model(
        entity: SubjectInfoEntity,
    ) -> SubjectInfo:

        if entity is None:
            raise ValueError(
                "SubjectInfoEntity must not be null"
            )

        SubjectInfoMapper._require_non_null(
            entity.identity_id,
            "identity_id",
        )

        SubjectInfoMapper._require_non_null(
            entity.subject_type,
            "subject_type",
        )

        SubjectInfoMapper._require_non_null(
            entity.name,
            "name",
        )

        SubjectInfoMapper._require_non_null(
            entity.updated_at,
            "updated_at",
        )

        return SubjectInfo(
            identity_id=entity.identity_id,
            subject_type=SubjectType(
                entity.subject_type,
            ),
            name=entity.name,
            updated_at=entity.updated_at,
        )

    # =========================
    # Model -> Entity
    # =========================

    @staticmethod
    def to_entity(
        model: SubjectInfo,
    ) -> SubjectInfoEntity:

        if model is None:
            raise ValueError(
                "SubjectInfo must not be null"
            )

        entity = SubjectInfoEntity()

        entity.identity_id = (
            model.identity_id
        )

        entity.subject_type = (
            model.subject_type.value
        )

        entity.name = (
            model.name
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