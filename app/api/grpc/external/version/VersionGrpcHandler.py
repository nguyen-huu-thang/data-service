import grpc

from app.api.grpc.generated.version_service_pb2_grpc import VersionServiceServicer
from app.api.grpc.mapper.VersionGrpcMapper import VersionGrpcMapper  # injected via DI
from app.application.service.authorization.JwtVerificationService import JwtVerificationService
from app.application.usecase.version.CreateVersionUseCase import CreateVersionUseCase
from app.application.usecase.version.DownloadVersionUseCase import DownloadVersionUseCase
from app.application.usecase.version.GetVersionUseCase import GetVersionUseCase
from app.application.usecase.version.ListVersionsUseCase import ListVersionsUseCase
from app.common.exception.AppException import PublicError

# Exceptions raised here propagate to AppExceptionInterceptor
# (app/api/grpc/interceptor/AppExceptionInterceptor.py), which redacts per the
# GRPC_INTERNAL channel and aborts with xime-error metadata. No per-method catch.
# Exception ném ở đây propagate tới AppExceptionInterceptor để che theo kênh
# GRPC_INTERNAL và abort kèm metadata xime-error. Không bắt lỗi theo từng method.


class VersionGrpcHandler(VersionServiceServicer):
    def __init__(
        self,
        create_version_use_case: CreateVersionUseCase,
        list_versions_use_case: ListVersionsUseCase,
        get_version_use_case: GetVersionUseCase,
        download_version_use_case: DownloadVersionUseCase,
        jwt_verification_service: JwtVerificationService,
        mapper: VersionGrpcMapper,
    ) -> None:
        self._create = create_version_use_case
        self._list = list_versions_use_case
        self._get = get_version_use_case
        self._download = download_version_use_case
        self._jwt = jwt_verification_service
        self._mapper = mapper

    @staticmethod
    def _extract_token(context: grpc.ServicerContext) -> str:
        metadata = dict(context.invocation_metadata())
        auth = metadata.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            raise PublicError("E007002", "Missing or invalid Authorization header")
        return auth[7:]

    async def CreateVersion(self, request, context):
        claims = await self._jwt.verify(self._extract_token(context))
        command = self._mapper.to_create_command(request, claims.identity_id, claims.subject_type, claims.name)
        result = await self._create.execute(command)
        return self._mapper.to_create_response(result)

    async def ListVersions(self, request, context):
        claims = await self._jwt.verify(self._extract_token(context))
        query = self._mapper.to_list_query(request, claims.identity_id, claims.subject_type, claims.name)
        versions = await self._list.execute(query)
        return self._mapper.to_list_response(versions)

    async def GetVersion(self, request, context):
        claims = await self._jwt.verify(self._extract_token(context))
        query = self._mapper.to_get_query(request, claims.identity_id, claims.subject_type, claims.name)
        version = await self._get.execute(query)
        return self._mapper.to_get_response(version)

    async def DownloadVersion(self, request, context):
        claims = await self._jwt.verify(self._extract_token(context))
        query = self._mapper.to_download_query(request, claims.identity_id, claims.subject_type, claims.name)
        result = await self._download.execute(query)
        return self._mapper.to_download_response(result)
