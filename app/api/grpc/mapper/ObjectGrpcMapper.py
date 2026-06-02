from app.api.grpc.generated.object_service_pb2 import (
    CreateObjectResponse,
    DeleteObjectResponse,
    DownloadObjectResponse,
    GetObjectResponse,
)
from app.application.dto.object.CreateObjectCommand import CreateObjectCommand
from app.application.dto.object.CreateObjectResult import CreateObjectResult
from app.application.dto.object.DeleteObjectCommand import DeleteObjectCommand
from app.application.dto.object.DownloadObjectQuery import DownloadObjectQuery
from app.application.dto.object.DownloadObjectResult import DownloadObjectResult
from app.application.dto.object.GetObjectQuery import GetObjectQuery
from app.common.constants.ObjectType import ObjectType
from app.common.constants.Visibility import Visibility
from app.domain.object.DataObject import DataObject


class ObjectGrpcMapper:
    def to_create_command(self, request, requester_identity_id: bytes) -> CreateObjectCommand:
        return CreateObjectCommand(
            requester_identity_id=requester_identity_id,
            object_type=ObjectType(request.object_type),
            visibility=Visibility(request.visibility),
            filename=request.filename,
            content_type=request.content_type,
            data=request.data,
            tenant_id=request.tenant_id or None,
        )

    def to_create_response(self, result: CreateObjectResult) -> CreateObjectResponse:
        return CreateObjectResponse(
            object_id=result.object_id,
            shard_id=result.shard_id,
            storage_pointer=result.storage_pointer,
        )

    def to_get_query(self, request, requester_identity_id: bytes) -> GetObjectQuery:
        return GetObjectQuery(
            requester_identity_id=requester_identity_id,
            object_id=request.object_id,
        )

    def to_get_response(self, obj: DataObject) -> GetObjectResponse:
        return GetObjectResponse(
            object_id=obj.object_id,
            owner_identity_id=obj.owner_identity_id,
            tenant_id=obj.tenant_id or "",
            shard_id=obj.shard_id,
            object_type=obj.object_type.value,
            visibility=obj.visibility.value,
            status=obj.status.value,
            storage_pointer=obj.storage_pointer,
            created_at_unix=int(obj.created_at.timestamp()),
            updated_at_unix=int(obj.updated_at.timestamp()),
        )

    def to_download_query(self, request, requester_identity_id: bytes) -> DownloadObjectQuery:
        return DownloadObjectQuery(
            requester_identity_id=requester_identity_id,
            object_id=request.object_id,
        )

    def to_download_response(self, result: DownloadObjectResult) -> DownloadObjectResponse:
        return DownloadObjectResponse(
            data=result.data,
            mime_type=result.mime_type,
            content_size=result.content_size,
        )

    def to_delete_command(self, request, requester_identity_id: bytes) -> DeleteObjectCommand:
        return DeleteObjectCommand(
            requester_identity_id=requester_identity_id,
            object_id=request.object_id,
        )

    @staticmethod
    def to_delete_response() -> DeleteObjectResponse:
        return DeleteObjectResponse(success=True)
