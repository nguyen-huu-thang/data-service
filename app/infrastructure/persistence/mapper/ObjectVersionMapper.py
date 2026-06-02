from app.domain.object.ObjectVersion import ObjectVersion
from app.infrastructure.persistence.entity.ObjectVersionEntity import ObjectVersionEntity


class ObjectVersionMapper:
    @staticmethod
    def to_domain(entity: ObjectVersionEntity) -> ObjectVersion:
        return ObjectVersion(
            version_id=entity.version_id,
            object_id=entity.object_id,
            version_number=entity.version_number,
            storage_pointer=entity.storage_pointer,
            content_hash=entity.content_hash,
            content_size=entity.content_size,
            mime_type=entity.mime_type,
            created_by=entity.created_by,
            created_at=entity.created_at,
        )

    @staticmethod
    def to_entity(domain: ObjectVersion) -> ObjectVersionEntity:
        return ObjectVersionEntity(
            version_id=domain.version_id,
            object_id=domain.object_id,
            version_number=domain.version_number,
            storage_pointer=domain.storage_pointer,
            content_hash=domain.content_hash,
            content_size=domain.content_size,
            mime_type=domain.mime_type,
            created_by=domain.created_by,
            created_at=domain.created_at,
        )
