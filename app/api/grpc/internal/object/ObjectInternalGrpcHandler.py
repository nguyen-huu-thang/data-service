import logging

import grpc

from app.api.grpc.internal.generated.object_internal_service_pb2 import PurgeObjectResponse
from app.api.grpc.internal.generated.object_internal_service_pb2_grpc import (
    ObjectInternalServiceServicer,
)
from app.application.dto.object.PurgeObjectCommand import PurgeObjectCommand
from app.application.usecase.object.PurgeObjectUseCase import PurgeObjectUseCase
from app.common.exception.InvalidObjectStateException import InvalidObjectStateException
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.common.exception.PermissionDeniedException import PermissionDeniedException

_log = logging.getLogger(__name__)


class ObjectInternalGrpcHandler(ObjectInternalServiceServicer):
    """
    Internal-only endpoint — caller identity verified via mTLS, not JWT.
    Do NOT expose on the public gRPC port.
    """

    def __init__(self, purge_object_use_case: PurgeObjectUseCase) -> None:
        self._purge = purge_object_use_case

    async def PurgeObject(self, request, context):
        try:
            command = PurgeObjectCommand(
                requester_identity_id=request.requester_identity_id,
                object_id=request.object_id,
            )
            await self._purge.execute(command)
            return PurgeObjectResponse(object_id=request.object_id)
        except ObjectNotFoundException:
            await context.abort(grpc.StatusCode.NOT_FOUND, "Object not found")
        except InvalidObjectStateException as e:
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(e))
        except PermissionDeniedException:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, "Permission denied")
        except Exception:
            _log.exception("Unexpected error in PurgeObject")
            await context.abort(grpc.StatusCode.INTERNAL, "Internal server error")
