from app.domain.object.model.ObjectVersion import ObjectVersion
from app.domain.object.valueobject.ContentHash import ContentHash
from app.domain.object.valueobject.MimeType import MimeType
from app.domain.subject.valueobject.SubjectType import SubjectType

from app.infrastructure.persistence.entity.ObjectVersionEntity import ObjectVersionEntity


class ObjectVersionMapper:

    # =========================
    # Entity -> Domain Model
    # =========================

    @staticmethod
    def to_domain(entity: ObjectVersionEntity) -> ObjectVersion:

        if entity is None:
            raise ValueError("ObjectVersionEntity must not be null")

        ObjectVersionMapper._require_non_null(entity.version_id, "version_id")
        ObjectVersionMapper._require_non_null(entity.object_id, "object_id")
        ObjectVersionMapper._require_non_null(entity.version_number, "version_number")
        ObjectVersionMapper._require_non_null(entity.storage_pointer, "storage_pointer")
        ObjectVersionMapper._require_non_null(entity.content_hash, "content_hash")
        ObjectVersionMapper._require_non_null(entity.content_size, "content_size")
        ObjectVersionMapper._require_non_null(entity.mime_type, "mime_type")
        ObjectVersionMapper._require_non_null(entity.created_by_identity_id, "created_by_identity_id")
        ObjectVersionMapper._require_non_null(entity.created_by_subject_type, "created_by_subject_type")
        ObjectVersionMapper._require_non_null(entity.created_at, "created_at")

        return ObjectVersion(
            version_id=entity.version_id,
            object_id=entity.object_id,
            version_number=entity.version_number,
            storage_pointer=entity.storage_pointer,
            content_hash=ContentHash(entity.content_hash),
            content_size=entity.content_size,
            mime_type=MimeType(entity.mime_type),
            created_by_identity_id=entity.created_by_identity_id,
            created_by_subject_type=SubjectType(entity.created_by_subject_type),
            created_at=entity.created_at,
        )

    # =========================
    # Domain Model -> Entity
    # =========================

    @staticmethod
    def to_entity(model: ObjectVersion) -> ObjectVersionEntity:

        if model is None:
            raise ValueError("ObjectVersion must not be null")

        entity = ObjectVersionEntity()

        entity.version_id = model.version_id
        entity.object_id = model.object_id
        entity.version_number = model.version_number
        entity.storage_pointer = model.storage_pointer
        entity.content_hash = model.content_hash.value
        entity.content_size = model.content_size
        entity.mime_type = model.mime_type.value
        entity.created_by_identity_id = model.created_by_identity_id
        entity.created_by_subject_type = str(model.created_by_subject_type)
        entity.created_at = model.created_at

        return entity

    # =========================
    # Helpers
    # =========================

    @staticmethod
    def _require_non_null(value: object, field: str) -> None:
        if value is None:
            raise ValueError(f"{field} must not be null")
