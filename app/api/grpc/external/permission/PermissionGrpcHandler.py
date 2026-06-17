import grpc

from app.api.grpc.generated.permission_service_pb2_grpc import PermissionServiceServicer
from app.application.dto.permission.GrantObjectPermissionCommand import GrantObjectPermissionCommand
from app.application.dto.permission.RevokeObjectPermissionCommand import RevokeObjectPermissionCommand
from app.application.service.authorization.JwtVerificationService import JwtVerificationService
from app.application.usecase.permission.GrantObjectPermissionUseCase import GrantObjectPermissionUseCase
from app.application.usecase.permission.RevokeObjectPermissionUseCase import RevokeObjectPermissionUseCase
from app.common.exception.AppException import PublicError
from app.domain.permission.role.Role import Role
from app.domain.sharedkernel.model.Id import Id

# Exceptions raised here propagate to AppExceptionInterceptor
# (app/api/grpc/interceptor/AppExceptionInterceptor.py), which redacts per the
# GRPC_INTERNAL channel and aborts with xime-error metadata. No per-method catch.
# Exception ném ở đây propagate tới AppExceptionInterceptor để che theo kênh
# GRPC_INTERNAL và abort kèm metadata xime-error. Không bắt lỗi theo từng method.


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
            raise PublicError("E007002", "Missing or invalid Authorization header")
        return auth[7:]

    @staticmethod
    def _parse_role(raw: str) -> Role:
        # A bad role value is client input — surface as a public 400.
        # Giá trị role sai là input của client - trả 400 public.
        try:
            return Role(raw)
        except ValueError as e:
            raise PublicError("E007001", str(e))

    async def GrantPermission(self, request, context):
        claims = await self._jwt.verify(self._extract_token(context))
        command = GrantObjectPermissionCommand(
            requester_identity_id=claims.identity_id,
            requester_subject_type=claims.subject_type,
            requester_name=claims.name,
            object_id=Id(request.object_id),
            target_identity_id=Id(request.target_identity_id),
            target_subject_type=request.target_subject_type or "HUMAN",
            role=self._parse_role(request.role),
        )
        await self._grant.execute(command)
        return self._make_grant_response()

    async def RevokePermission(self, request, context):
        claims = await self._jwt.verify(self._extract_token(context))
        command = RevokeObjectPermissionCommand(
            requester_identity_id=claims.identity_id,
            requester_subject_type=claims.subject_type,
            requester_name=claims.name,
            object_id=Id(request.object_id),
            target_identity_id=Id(request.target_identity_id),
        )
        await self._revoke.execute(command)
        return self._make_revoke_response()

    async def ListPermissions(self, request, context):
        await context.abort(grpc.StatusCode.UNIMPLEMENTED, "ListPermissions not yet implemented")

    @staticmethod
    def _make_grant_response():
        from app.api.grpc.generated.permission_service_pb2 import GrantPermissionResponse

        return GrantPermissionResponse(success=True)

    @staticmethod
    def _make_revoke_response():
        from app.api.grpc.generated.permission_service_pb2 import RevokePermissionResponse

        return RevokePermissionResponse(success=True)
