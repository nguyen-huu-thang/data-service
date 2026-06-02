import logging

import grpc

from app.api.grpc.generated.object_service_pb2_grpc import ObjectServiceServicer
from app.api.grpc.mapper.ObjectGrpcMapper import ObjectGrpcMapper
from app.application.service.authorization.JwtVerificationService import JwtVerificationService
from app.application.usecase.object.CreateObjectUseCase import CreateObjectUseCase
from app.application.usecase.object.DeleteObjectUseCase import DeleteObjectUseCase
from app.application.usecase.object.DownloadObjectUseCase import DownloadObjectUseCase
from app.application.usecase.object.GetObjectUseCase import GetObjectUseCase
from app.common.exception.InvalidTokenException import InvalidTokenException
from app.common.exception.ObjectAlreadyDeletedException import ObjectAlreadyDeletedException
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.common.exception.PermissionDeniedException import PermissionDeniedException

_log = logging.getLogger(__name__)


class ObjectGrpcHandler(ObjectServiceServicer):
    def __init__(
        self,
        create_object_use_case: CreateObjectUseCase,
        get_object_use_case: GetObjectUseCase,
        download_object_use_case: DownloadObjectUseCase,
        delete_object_use_case: DeleteObjectUseCase,
        jwt_verification_service: JwtVerificationService,
    ) -> None:
        self._create = create_object_use_case
        self._get = get_object_use_case
        self._download = download_object_use_case
        self._delete = delete_object_use_case
        self._jwt = jwt_verification_service
        self._mapper = ObjectGrpcMapper()  # utility class, not DI-managed

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _extract_token(context: grpc.ServicerContext) -> str:
        metadata = dict(context.invocation_metadata())
        auth = metadata.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            raise InvalidTokenException("Missing or invalid Authorization header")
        return auth[7:]

    # ── Handlers ─────────────────────────────────────────────────────────

    async def CreateObject(self, request, context):
        try:
            claims = await self._jwt.verify(self._extract_token(context))
            command = self._mapper.to_create_command(request, claims.identity_id)
            result = await self._create.execute(command)
            return self._mapper.to_create_response(result)
        except InvalidTokenException as e:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, str(e))
        except PermissionDeniedException:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, "Permission denied")
        except Exception:
            _log.exception("Unexpected error in CreateObject")
            await context.abort(grpc.StatusCode.INTERNAL, "Internal server error")

    async def GetObject(self, request, context):
        try:
            claims = await self._jwt.verify(self._extract_token(context))
            query = self._mapper.to_get_query(request, claims.identity_id)
            obj = await self._get.execute(query)
            return self._mapper.to_get_response(obj)
        except InvalidTokenException as e:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, str(e))
        except ObjectNotFoundException:
            await context.abort(grpc.StatusCode.NOT_FOUND, "Object not found")
        except PermissionDeniedException:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, "Permission denied")
        except Exception:
            _log.exception("Unexpected error in GetObject")
            await context.abort(grpc.StatusCode.INTERNAL, "Internal server error")

    async def DownloadObject(self, request, context):
        try:
            claims = await self._jwt.verify(self._extract_token(context))
            query = self._mapper.to_download_query(request, claims.identity_id)
            result = await self._download.execute(query)
            return self._mapper.to_download_response(result)
        except InvalidTokenException as e:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, str(e))
        except ObjectNotFoundException:
            await context.abort(grpc.StatusCode.NOT_FOUND, "Object not found")
        except PermissionDeniedException:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, "Permission denied")
        except Exception:
            _log.exception("Unexpected error in DownloadObject")
            await context.abort(grpc.StatusCode.INTERNAL, "Internal server error")

    async def DeleteObject(self, request, context):
        try:
            claims = await self._jwt.verify(self._extract_token(context))
            command = self._mapper.to_delete_command(request, claims.identity_id)
            await self._delete.execute(command)
            return self._mapper.to_delete_response()
        except InvalidTokenException as e:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, str(e))
        except ObjectNotFoundException:
            await context.abort(grpc.StatusCode.NOT_FOUND, "Object not found")
        except ObjectAlreadyDeletedException:
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Object is already deleted")
        except PermissionDeniedException:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, "Permission denied")
        except Exception:
            _log.exception("Unexpected error in DeleteObject")
            await context.abort(grpc.StatusCode.INTERNAL, "Internal server error")
