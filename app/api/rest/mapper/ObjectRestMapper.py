from pydantic import BaseModel

from app.application.dto.object.CreateObjectResult import CreateObjectResult
from app.domain.object.DataObject import DataObject


class CreateObjectResponse(BaseModel):
    object_id: str
    shard_id: str
    storage_pointer: str


class ObjectResponse(BaseModel):
    object_id: str
    owner_identity_id: str
    tenant_id: str | None
    shard_id: str
    object_type: str
    visibility: str
    status: str
    created_at: str
    updated_at: str


class ObjectStatusResponse(BaseModel):
    object_id: str
    status: str


class ObjectRestMapper:
    def to_create_response(self, result: CreateObjectResult) -> CreateObjectResponse:
        return CreateObjectResponse(
            object_id=result.object_id.hex(),
            shard_id=result.shard_id,
            storage_pointer=result.storage_pointer,
        )

    def to_object_response(self, obj: DataObject) -> ObjectResponse:
        return ObjectResponse(
            object_id=obj.object_id.hex(),
            owner_identity_id=obj.owner_identity_id.hex(),
            tenant_id=obj.tenant_id,
            shard_id=obj.shard_id,
            object_type=obj.object_type.value,
            visibility=obj.visibility.value,
            status=obj.status.value,
            created_at=obj.created_at.isoformat(),
            updated_at=obj.updated_at.isoformat(),
        )

    def to_archive_response(self, object_id: bytes) -> ObjectStatusResponse:
        return ObjectStatusResponse(object_id=object_id.hex(), status="ARCHIVED")

    def to_restore_response(self, object_id: bytes) -> ObjectStatusResponse:
        return ObjectStatusResponse(object_id=object_id.hex(), status="ACTIVE")
