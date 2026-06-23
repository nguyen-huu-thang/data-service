import grpc
from xime.starters.storage import StorageService

from app.api.grpc.generated.object_service_pb2 import ArchiveObjectResponse, RestoreObjectResponse
from app.api.grpc.generated.object_service_pb2_grpc import ObjectServiceServicer
from app.api.grpc.mapper.ObjectGrpcMapper import ObjectGrpcMapper
from app.application.dto.object.ArchiveObjectCommand import ArchiveObjectCommand
from app.application.dto.object.RestoreObjectCommand import RestoreObjectCommand
from app.application.service.authorization.JwtVerificationService import JwtVerificationService
from app.application.usecase.object.ArchiveObjectUseCase import ArchiveObjectUseCase
from app.application.usecase.object.CreateObjectUseCase import CreateObjectUseCase
from app.application.usecase.object.DeleteObjectUseCase import DeleteObjectUseCase
from app.application.usecase.object.DownloadObjectUseCase import DownloadObjectUseCase
from app.application.usecase.object.GetObjectUseCase import GetObjectUseCase
from app.application.usecase.object.RestoreObjectUseCase import RestoreObjectUseCase
from app.common.exception.AppException import PrivateError, PublicError
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.sharedkernel.model.Id import Id

# Exceptions raised here propagate to AppExceptionInterceptor
# (app/api/grpc/interceptor/AppExceptionInterceptor.py), which redacts per the
# GRPC_INTERNAL channel and aborts with xime-error metadata. No per-method catch.
# Exception ném ở đây propagate tới AppExceptionInterceptor để che theo kênh
# GRPC_INTERNAL và abort kèm metadata xime-error. Không bắt lỗi theo từng method.


class ObjectGrpcHandler(ObjectServiceServicer):
    def __init__(
        self,
        create_object_use_case: CreateObjectUseCase,
        get_object_use_case: GetObjectUseCase,
        download_object_use_case: DownloadObjectUseCase,
        delete_object_use_case: DeleteObjectUseCase,
        archive_object_use_case: ArchiveObjectUseCase,
        restore_object_use_case: RestoreObjectUseCase,
        jwt_verification_service: JwtVerificationService,
        storage: StorageService,
        mapper: ObjectGrpcMapper,
    ) -> None:
        self._create = create_object_use_case
        self._get = get_object_use_case
        self._download = download_object_use_case
        self._delete = delete_object_use_case
        self._archive = archive_object_use_case
        self._restore = restore_object_use_case
        self._jwt = jwt_verification_service
        self._storage = storage
        self._mapper = mapper

    @staticmethod
    def _extract_token(context: grpc.ServicerContext) -> str:
        metadata = dict(context.invocation_metadata())
        auth = metadata.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            raise PublicError("E007002", "Missing or invalid Authorization header")
        return auth[7:]

    async def CreateObject(self, request, context):
        claims = await self._jwt.verify(self._extract_token(context))
        command = self._mapper.to_create_command(
            request, claims.identity_id, claims.subject_type, claims.name
        )
        result = await self._create.execute(command)
        return self._mapper.to_create_response(result)

    async def GetObject(self, request, context):
        claims = await self._jwt.verify(self._extract_token(context))
        query = self._mapper.to_get_query(
            request, claims.identity_id, claims.subject_type, claims.name
        )
        obj = await self._get.execute(query)
        return self._mapper.to_get_response(obj)

    async def DownloadObject(self, request, context):
        claims = await self._jwt.verify(self._extract_token(context))
        query = self._mapper.to_download_query(
            request, claims.identity_id, claims.subject_type, claims.name
        )
        # The use case authorizes + audits and resolves the blob location; the
        # unary gRPC contract returns the whole blob, so load it here.
        # Usecase authz + audit và phân giải vị trí blob; hợp đồng gRPC unary trả
        # cả blob nên tải bytes ở đây.
        result = await self._download.execute(query)
        data = await self._storage.get(result.storage_pointer)
        if data is None:
            # Metadata exists but the blob is missing — internal inconsistency.
            # Metadata còn nhưng blob mất - lỗi nội bộ không nhất quán.
            raise PrivateError("E060002")
        return self._mapper.to_download_response(data, result.mime_type)

    async def DeleteObject(self, request, context):
        claims = await self._jwt.verify(self._extract_token(context))
        command = self._mapper.to_delete_command(
            request, claims.identity_id, claims.subject_type, claims.name
        )
        await self._delete.execute(command)
        return self._mapper.to_delete_response()

    async def ArchiveObject(self, request, context):
        claims = await self._jwt.verify(self._extract_token(context))
        command = ArchiveObjectCommand(
            requester_identity_id=claims.identity_id,
            requester_subject_type=claims.subject_type,
            requester_name=claims.name,
            object_id=Id(request.object_id),
        )
        await self._archive.execute(command)
        return ArchiveObjectResponse(
            object_id=request.object_id,
            status=ObjectStatus.ARCHIVED.value,
        )

    async def RestoreObject(self, request, context):
        claims = await self._jwt.verify(self._extract_token(context))
        command = RestoreObjectCommand(
            requester_identity_id=claims.identity_id,
            requester_subject_type=claims.subject_type,
            requester_name=claims.name,
            object_id=Id(request.object_id),
        )
        await self._restore.execute(command)
        return RestoreObjectResponse(
            object_id=request.object_id,
            status=ObjectStatus.ACTIVE.value,
        )
