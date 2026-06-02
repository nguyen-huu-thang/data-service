import logging

import grpc.aio
from core.config.runtime import RuntimeConfig

from app.api.grpc.external.object.ObjectGrpcHandler import ObjectGrpcHandler
from app.api.grpc.external.permission.PermissionGrpcHandler import PermissionGrpcHandler
from app.api.grpc.generated.object_service_pb2_grpc import add_ObjectServiceServicer_to_server
from app.api.grpc.generated.permission_service_pb2_grpc import add_PermissionServiceServicer_to_server

_log = logging.getLogger(__name__)


class GrpcAdapter:
    """
    Xime Adapter — wraps grpc.aio.server lifecycle.

    Registered via app.use(GrpcAdapter()); started concurrently by app.run().
    Blocks inside start() until the server is terminated (graceful or forced).
    stop() signals the gRPC server to shut down with a grace period.
    """

    def __init__(self) -> None:
        self._server: grpc.aio.Server | None = None

    async def start(self, app) -> None:
        port: int = app.get(RuntimeConfig).get("grpc.port", 50051)

        self._server = grpc.aio.server()

        add_ObjectServiceServicer_to_server(
            app.get(ObjectGrpcHandler), self._server
        )
        add_PermissionServiceServicer_to_server(
            app.get(PermissionGrpcHandler), self._server
        )

        self._server.add_insecure_port(f"[::]:{port}")
        await self._server.start()
        _log.info("Data Service gRPC server listening on port %s", port)
        await self._server.wait_for_termination()

    async def stop(self) -> None:
        if self._server is not None:
            _log.info("Stopping gRPC server (grace=5s)...")
            await self._server.stop(grace=5)
            self._server = None
