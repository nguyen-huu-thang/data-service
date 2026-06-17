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
from app.domain.object.model.DataObject import DataObject
from app.domain.object.valueobject.ObjectType import ObjectType
from app.domain.object.valueobject.ObjectVisibility import ObjectVisibility
from app.domain.sharedkernel.model.Id import Id


class ObjectGrpcMapper:
    # Internal gRPC carries ids as raw bytes on the wire; convert to/from Id here.
    # gRPC nội bộ truyền id dạng bytes; chuyển đổi <-> Id tại đây.
    def to_create_command(
        self,
        request,
        requester_identity_id: Id,
        requester_subject_type: str = "HUMAN",
        requester_name: str = "",
    ) -> CreateObjectCommand:
        return CreateObjectCommand(
            requester_identity_id=requester_identity_id,
            requester_subject_type=requester_subject_type,
            requester_name=requester_name,
            object_type=ObjectType(request.object_type),
            visibility=ObjectVisibility(request.visibility),
            filename=request.filename,
            content_type=request.content_type,
            data=request.data,
            tenant_id=request.tenant_id or None,
        )

    def to_create_response(self, result: CreateObjectResult) -> CreateObjectResponse:
        return CreateObjectResponse(
            object_id=result.object_id.to_bytes(),
            shard_id=result.shard_id,
            storage_pointer=result.storage_pointer,
        )

    def to_get_query(
        self,
        request,
        requester_identity_id: Id,
        requester_subject_type: str = "HUMAN",
        requester_name: str = "",
    ) -> GetObjectQuery:
        return GetObjectQuery(
            requester_identity_id=requester_identity_id,
            requester_subject_type=requester_subject_type,
            requester_name=requester_name,
            object_id=Id(request.object_id),
        )

    def to_get_response(self, obj: DataObject) -> GetObjectResponse:
        return GetObjectResponse(
            object_id=obj.object_id.to_bytes(),
            owner_identity_id=obj.owner_identity_id.to_bytes(),
            tenant_id=obj.tenant_id or "",
            shard_id=obj.shard_id,
            object_type=obj.object_type.value,
            visibility=obj.visibility.value,
            status=obj.status.value,
            storage_pointer=obj.storage_pointer,
            created_at_unix=int(obj.created_at.timestamp()),
            updated_at_unix=int(obj.updated_at.timestamp()),
        )

    def to_download_query(
        self,
        request,
        requester_identity_id: Id,
        requester_subject_type: str = "HUMAN",
        requester_name: str = "",
    ) -> DownloadObjectQuery:
        return DownloadObjectQuery(
            requester_identity_id=requester_identity_id,
            requester_subject_type=requester_subject_type,
            requester_name=requester_name,
            object_id=Id(request.object_id),
        )

    def to_download_response(self, result: DownloadObjectResult) -> DownloadObjectResponse:
        return DownloadObjectResponse(
            data=result.data,
            mime_type=result.mime_type,
            content_size=result.content_size,
        )

    def to_delete_command(
        self,
        request,
        requester_identity_id: Id,
        requester_subject_type: str = "HUMAN",
        requester_name: str = "",
    ) -> DeleteObjectCommand:
        return DeleteObjectCommand(
            requester_identity_id=requester_identity_id,
            requester_subject_type=requester_subject_type,
            requester_name=requester_name,
            object_id=Id(request.object_id),
        )

    @staticmethod
    def to_delete_response() -> DeleteObjectResponse:
        return DeleteObjectResponse(success=True)
