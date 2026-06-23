from xime.core.security import current_caller

from app.api.grpc.internal.generated.object_internal_service_pb2 import PurgeObjectResponse
from app.api.grpc.internal.generated.object_internal_service_pb2_grpc import (
    ObjectInternalServiceServicer,
)
from app.application.dto.object.PurgeObjectCommand import PurgeObjectCommand
from app.application.service.authorization.InternalCallerAuthorizer import InternalCallerAuthorizer
from app.application.usecase.object.PurgeObjectUseCase import PurgeObjectUseCase
from app.domain.sharedkernel.model.Id import Id

# Exceptions raised here propagate to AppExceptionInterceptor
# (app/api/grpc/interceptor/AppExceptionInterceptor.py), which redacts per the
# GRPC_INTERNAL channel and aborts with xime-error metadata. No per-method catch.
# Exception ném ở đây propagate tới AppExceptionInterceptor để che theo kênh
# GRPC_INTERNAL và abort kèm metadata xime-error. Không bắt lỗi theo từng method.


class ObjectInternalGrpcHandler(ObjectInternalServiceServicer):
    """
    Internal-only endpoint — caller identity verified via mTLS, not JWT.
    Do NOT expose on the public gRPC port.

    The mTLS peer Common Name (from the client certificate) is resolved by the
    framework interceptor; InternalCallerAuthorizer enforces it against the
    configured allowlist before any destructive work runs.
    CN của peer mTLS (từ client cert) do interceptor framework phân giải;
    InternalCallerAuthorizer ép khớp allowlist trước khi chạy thao tác phá hủy.
    """

    def __init__(
        self,
        purge_object_use_case: PurgeObjectUseCase,
        caller_authorizer: InternalCallerAuthorizer,
    ) -> None:
        self._purge = purge_object_use_case
        self._caller_authorizer = caller_authorizer

    async def PurgeObject(self, request, context):
        # Authorize the mTLS caller before doing anything destructive. Purge is
        # irreversible, so an untrusted caller must never reach the use case.
        # Authorize caller mTLS trước khi làm gì phá hủy. Purge không thể hoàn tác
        # nên caller không tin cậy không bao giờ được chạm tới usecase.
        self._caller_authorizer.authorize(current_caller())
        command = PurgeObjectCommand(
            requester_identity_id=Id(request.requester_identity_id),
            requester_subject_type=getattr(request, "requester_subject_type", "APPLICATION"),
            requester_name=getattr(request, "requester_name", ""),
            object_id=Id(request.object_id),
        )
        await self._purge.execute(command)
        return PurgeObjectResponse(object_id=request.object_id)
