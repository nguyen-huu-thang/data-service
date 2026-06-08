from app.domain.object.model.DataObject import DataObject
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.object.valueobject.ObjectType import ObjectType
from app.domain.object.valueobject.ObjectVisibility import ObjectVisibility

from app.infrastructure.persistence.entity.DataObjectEntity import DataObjectEntity


class DataObjectMapper:

    # =========================
    # Entity -> Domain Model
    # =========================

    @staticmethod
    def to_domain(entity: DataObjectEntity) -> DataObject:

        if entity is None:
            raise ValueError("DataObjectEntity must not be null")

        DataObjectMapper._require_non_null(entity.object_id, "object_id")
        DataObjectMapper._require_non_null(entity.shard_id, "shard_id")
        DataObjectMapper._require_non_null(entity.owner_identity_id, "owner_identity_id")
        DataObjectMapper._require_non_null(entity.owner_subject_type, "owner_subject_type")
        DataObjectMapper._require_non_null(entity.object_type, "object_type")
        DataObjectMapper._require_non_null(entity.visibility, "visibility")
        DataObjectMapper._require_non_null(entity.status, "status")
        DataObjectMapper._require_non_null(entity.storage_provider, "storage_provider")
        DataObjectMapper._require_non_null(entity.storage_pointer, "storage_pointer")
        DataObjectMapper._require_non_null(entity.permission_version, "permission_version")
        DataObjectMapper._require_non_null(entity.created_at, "created_at")
        DataObjectMapper._require_non_null(entity.updated_at, "updated_at")

        return DataObject(
            object_id=entity.object_id,
            tenant_id=entity.tenant_id,
            shard_id=entity.shard_id,
            owner_identity_id=entity.owner_identity_id,
            owner_subject_type=entity.owner_subject_type,
            object_type=ObjectType(entity.object_type),
            visibility=ObjectVisibility(entity.visibility),
            status=ObjectStatus(entity.status),
            current_version_id=entity.current_version_id,
            storage_provider=entity.storage_provider,
            storage_pointer=entity.storage_pointer,
            metadata=entity.metadata_json,
            permission_version=entity.permission_version,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    # =========================
    # Domain Model -> Entity
    # =========================

    @staticmethod
    def to_entity(model: DataObject) -> DataObjectEntity:

        if model is None:
            raise ValueError("DataObject must not be null")

        entity = DataObjectEntity()

        entity.object_id = model.object_id
        entity.tenant_id = model.tenant_id
        entity.shard_id = model.shard_id
        entity.owner_identity_id = model.owner_identity_id
        entity.owner_subject_type = model.owner_subject_type
        entity.object_type = model.object_type.value
        entity.visibility = model.visibility.value
        entity.status = model.status.value
        entity.current_version_id = model.current_version_id
        entity.storage_provider = model.storage_provider
        entity.storage_pointer = model.storage_pointer
        entity.metadata_json = model.metadata
        entity.permission_version = model.permission_version
        entity.created_at = model.created_at
        entity.updated_at = model.updated_at

        return entity

    # =========================
    # Helpers
    # =========================

    @staticmethod
    def _require_non_null(value: object, field: str) -> None:
        if value is None:
            raise ValueError(f"{field} must not be null")
