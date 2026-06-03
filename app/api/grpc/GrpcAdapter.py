import logging

import grpc.aio
from xime.core.config.runtime import RuntimeConfig

from app.api.grpc.external.object.ObjectGrpcHandler import ObjectGrpcHandler
from app.api.grpc.external.permission.PermissionGrpcHandler import PermissionGrpcHandler
from app.api.grpc.external.version.VersionGrpcHandler import VersionGrpcHandler
from app.api.grpc.internal.object.ObjectInternalGrpcHandler import ObjectInternalGrpcHandler
from app.api.grpc.generated.object_service_pb2_grpc import add_ObjectServiceServicer_to_server
from app.api.grpc.generated.permission_service_pb2_grpc import add_PermissionServiceServicer_to_server
from app.api.grpc.generated.version_service_pb2_grpc import add_VersionServiceServicer_to_server
from app.api.grpc.internal.generated.object_internal_service_pb2_grpc import (
    add_ObjectInternalServiceServicer_to_server,
)

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
        internal_port: int = app.get(RuntimeConfig).get("grpc.internal_port", 50052)

        self._server = grpc.aio.server()

        add_ObjectServiceServicer_to_server(
            app.get(ObjectGrpcHandler), self._server
        )
        add_PermissionServiceServicer_to_server(
            app.get(PermissionGrpcHandler), self._server
        )
        add_VersionServiceServicer_to_server(
            app.get(VersionGrpcHandler), self._server
        )
        add_ObjectInternalServiceServicer_to_server(
            app.get(ObjectInternalGrpcHandler), self._server
        )

        self._server.add_insecure_port(f"[::]:{port}")
        # Internal port — should be restricted to service mesh / mTLS in production
        self._server.add_insecure_port(f"[::]:{internal_port}")
        await self._server.start()
        _log.info(
            "Data Service gRPC server listening on port %s (internal: %s)",
            port,
            internal_port,
        )
        await self._server.wait_for_termination()

    async def stop(self) -> None:
        if self._server is not None:
            _log.info("Stopping gRPC server (grace=5s)...")
            await self._server.stop(grace=5)
            self._server = None
