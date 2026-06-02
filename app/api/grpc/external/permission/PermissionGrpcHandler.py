import grpc

from app.api.grpc.generated.permission_service_pb2_grpc import PermissionServiceServicer


class PermissionGrpcHandler(PermissionServiceServicer):
    """Placeholder handler — use cases will be implemented in Phase 11."""

    def __init__(self) -> None:
        pass

    async def GrantPermission(self, request, context):
        await context.abort(grpc.StatusCode.UNIMPLEMENTED, "GrantPermission not yet implemented")

    async def RevokePermission(self, request, context):
        await context.abort(grpc.StatusCode.UNIMPLEMENTED, "RevokePermission not yet implemented")

    async def ListPermissions(self, request, context):
        await context.abort(grpc.StatusCode.UNIMPLEMENTED, "ListPermissions not yet implemented")
