from app.api.grpc.internal.generated.object_internal_service_pb2 import PurgeObjectResponse
from app.api.grpc.internal.generated.object_internal_service_pb2_grpc import (
    ObjectInternalServiceServicer,
)
from app.application.dto.object.PurgeObjectCommand import PurgeObjectCommand
from app.application.usecase.object.PurgeObjectUseCase import PurgeObjectUseCase

# Exceptions raised here propagate to AppExceptionInterceptor
# (app/api/grpc/interceptor/AppExceptionInterceptor.py), which redacts per the
# GRPC_INTERNAL channel and aborts with xime-error metadata. No per-method catch.
# Exception ném ở đây propagate tới AppExceptionInterceptor để che theo kênh
# GRPC_INTERNAL và abort kèm metadata xime-error. Không bắt lỗi theo từng method.


class ObjectInternalGrpcHandler(ObjectInternalServiceServicer):
    """
    Internal-only endpoint — caller identity verified via mTLS, not JWT.
    Do NOT expose on the public gRPC port.
    """

    def __init__(self, purge_object_use_case: PurgeObjectUseCase) -> None:
        self._purge = purge_object_use_case

    async def PurgeObject(self, request, context):
        command = PurgeObjectCommand(
            requester_identity_id=request.requester_identity_id,
            requester_subject_type=getattr(request, "requester_subject_type", "APPLICATION"),
            requester_name=getattr(request, "requester_name", ""),
            object_id=request.object_id,
        )
        await self._purge.execute(command)
        return PurgeObjectResponse(object_id=request.object_id)
