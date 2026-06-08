import logging

import grpc

from app.api.grpc.generated.permission_service_pb2_grpc import PermissionServiceServicer
from app.application.dto.permission.GrantObjectPermissionCommand import GrantObjectPermissionCommand
from app.application.dto.permission.RevokeObjectPermissionCommand import RevokeObjectPermissionCommand
from app.application.service.authorization.JwtVerificationService import JwtVerificationService
from app.application.usecase.permission.GrantObjectPermissionUseCase import GrantObjectPermissionUseCase
from app.application.usecase.permission.RevokeObjectPermissionUseCase import RevokeObjectPermissionUseCase
from app.common.exception.InvalidTokenException import InvalidTokenException
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.common.exception.PermissionDeniedException import PermissionDeniedException
from app.domain.permission.role.Role import Role

_log = logging.getLogger(__name__)


class PermissionGrpcHandler(PermissionServiceServicer):
    def __init__(
        self,
        grant_object_permission_use_case: GrantObjectPermissionUseCase,
        revoke_object_permission_use_case: RevokeObjectPermissionUseCase,
        jwt_verification_service: JwtVerificationService,
    ) -> None:
        self._grant = grant_object_permission_use_case
        self._revoke = revoke_object_permission_use_case
        self._jwt = jwt_verification_service

    @staticmethod
    def _extract_token(context: grpc.ServicerContext) -> str:
        metadata = dict(context.invocation_metadata())
        auth = metadata.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            raise InvalidTokenException("Missing or invalid Authorization header")
        return auth[7:]

    async def GrantPermission(self, request, context):
        try:
            claims = await self._jwt.verify(self._extract_token(context))
            command = GrantObjectPermissionCommand(
                requester_identity_id=claims.identity_id,
                requester_subject_type=claims.subject_type,
                requester_name=claims.name,
                object_id=request.object_id,
                target_identity_id=request.target_identity_id,
                target_subject_type=request.target_subject_type or "HUMAN",
                role=Role(request.role),
            )
            await self._grant.execute(command)
            return self._make_grant_response()
        except InvalidTokenException as e:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, str(e))
        except ObjectNotFoundException:
            await context.abort(grpc.StatusCode.NOT_FOUND, "Object not found")
        except PermissionDeniedException:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, "Permission denied")
        except ValueError as e:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
        except Exception:
            _log.exception("Unexpected error in GrantPermission")
            await context.abort(grpc.StatusCode.INTERNAL, "Internal server error")

    async def RevokePermission(self, request, context):
        try:
            claims = await self._jwt.verify(self._extract_token(context))
            command = RevokeObjectPermissionCommand(
                requester_identity_id=claims.identity_id,
                requester_subject_type=claims.subject_type,
                requester_name=claims.name,
                object_id=request.object_id,
                target_identity_id=request.target_identity_id,
            )
            await self._revoke.execute(command)
            return self._make_revoke_response()
        except InvalidTokenException as e:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, str(e))
        except ObjectNotFoundException:
            await context.abort(grpc.StatusCode.NOT_FOUND, "Object not found")
        except PermissionDeniedException:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, "Permission denied")
        except Exception:
            _log.exception("Unexpected error in RevokePermission")
            await context.abort(grpc.StatusCode.INTERNAL, "Internal server error")

    async def ListPermissions(self, request, context):
        await context.abort(grpc.StatusCode.UNIMPLEMENTED, "ListPermissions not yet implemented")

    @staticmethod
    def _make_grant_response():
        try:
            from app.api.grpc.generated.permission_service_pb2 import GrantPermissionResponse
            return GrantPermissionResponse(success=True)
        except Exception:
            return None

    @staticmethod
    def _make_revoke_response():
        try:
            from app.api.grpc.generated.permission_service_pb2 import RevokePermissionResponse
            return RevokePermissionResponse(success=True)
        except Exception:
            return None
