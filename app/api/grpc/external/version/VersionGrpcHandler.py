import logging

import grpc

from app.api.grpc.generated.version_service_pb2_grpc import VersionServiceServicer
from app.api.grpc.mapper.VersionGrpcMapper import VersionGrpcMapper  # injected via DI
from app.application.service.authorization.JwtVerificationService import JwtVerificationService
from app.application.usecase.version.CreateVersionUseCase import CreateVersionUseCase
from app.application.usecase.version.DownloadVersionUseCase import DownloadVersionUseCase
from app.application.usecase.version.GetVersionUseCase import GetVersionUseCase
from app.application.usecase.version.ListVersionsUseCase import ListVersionsUseCase
from app.common.exception.InvalidObjectStateException import InvalidObjectStateException
from app.common.exception.InvalidTokenException import InvalidTokenException
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.common.exception.PermissionDeniedException import PermissionDeniedException

_log = logging.getLogger(__name__)


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
            raise InvalidTokenException("Missing or invalid Authorization header")
        return auth[7:]

    async def CreateVersion(self, request, context):
        try:
            claims = await self._jwt.verify(self._extract_token(context))
            command = self._mapper.to_create_command(request, claims.identity_id, claims.subject_type, claims.name)
            result = await self._create.execute(command)
            return self._mapper.to_create_response(result)
        except InvalidTokenException as e:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, str(e))
        except ObjectNotFoundException:
            await context.abort(grpc.StatusCode.NOT_FOUND, "Object not found")
        except InvalidObjectStateException as e:
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(e))
        except PermissionDeniedException:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, "Permission denied")
        except Exception:
            _log.exception("Unexpected error in CreateVersion")
            await context.abort(grpc.StatusCode.INTERNAL, "Internal server error")

    async def ListVersions(self, request, context):
        try:
            claims = await self._jwt.verify(self._extract_token(context))
            query = self._mapper.to_list_query(request, claims.identity_id, claims.subject_type, claims.name)
            versions = await self._list.execute(query)
            return self._mapper.to_list_response(versions)
        except InvalidTokenException as e:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, str(e))
        except ObjectNotFoundException:
            await context.abort(grpc.StatusCode.NOT_FOUND, "Object not found")
        except PermissionDeniedException:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, "Permission denied")
        except Exception:
            _log.exception("Unexpected error in ListVersions")
            await context.abort(grpc.StatusCode.INTERNAL, "Internal server error")

    async def GetVersion(self, request, context):
        try:
            claims = await self._jwt.verify(self._extract_token(context))
            query = self._mapper.to_get_query(request, claims.identity_id, claims.subject_type, claims.name)
            version = await self._get.execute(query)
            return self._mapper.to_get_response(version)
        except InvalidTokenException as e:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, str(e))
        except ObjectNotFoundException:
            await context.abort(grpc.StatusCode.NOT_FOUND, "Object or version not found")
        except PermissionDeniedException:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, "Permission denied")
        except Exception:
            _log.exception("Unexpected error in GetVersion")
            await context.abort(grpc.StatusCode.INTERNAL, "Internal server error")

    async def DownloadVersion(self, request, context):
        try:
            claims = await self._jwt.verify(self._extract_token(context))
            query = self._mapper.to_download_query(request, claims.identity_id, claims.subject_type, claims.name)
            result = await self._download.execute(query)
            return self._mapper.to_download_response(result)
        except InvalidTokenException as e:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, str(e))
        except ObjectNotFoundException:
            await context.abort(grpc.StatusCode.NOT_FOUND, "Object or version not found")
        except PermissionDeniedException:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, "Permission denied")
        except Exception:
            _log.exception("Unexpected error in DownloadVersion")
            await context.abort(grpc.StatusCode.INTERNAL, "Internal server error")
