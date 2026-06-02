from app.common.constants.ObjectStatus import ObjectStatus
from app.common.constants.ObjectType import ObjectType
from app.common.constants.Visibility import Visibility
from app.domain.object.DataObject import DataObject
from app.infrastructure.persistence.entity.DataObjectEntity import DataObjectEntity


class DataObjectMapper:
    @staticmethod
    def to_domain(entity: DataObjectEntity) -> DataObject:
        return DataObject(
            object_id=entity.object_id,
            owner_identity_id=entity.owner_identity_id,
            tenant_id=entity.tenant_id,
            shard_id=entity.shard_id,
            object_type=ObjectType(entity.object_type),
            visibility=Visibility(entity.visibility),
            status=ObjectStatus(entity.status),
            storage_provider=entity.storage_provider,
            storage_pointer=entity.storage_pointer,
            metadata_json=entity.metadata_json or {},
            permission_version=entity.permission_version,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            current_version_id=entity.current_version_id,
        )

    @staticmethod
    def to_entity(domain: DataObject) -> DataObjectEntity:
        return DataObjectEntity(
            object_id=domain.object_id,
            owner_identity_id=domain.owner_identity_id,
            tenant_id=domain.tenant_id,
            shard_id=domain.shard_id,
            object_type=domain.object_type.value,
            visibility=domain.visibility.value,
            status=domain.status.value,
            storage_provider=domain.storage_provider,
            storage_pointer=domain.storage_pointer,
            metadata_json=domain.metadata_json if domain.metadata_json else None,
            permission_version=domain.permission_version,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
            current_version_id=domain.current_version_id,
        )
