from xime.adapters.grpc import configure_grpc_services

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

configure_grpc_services(
    packages=["app.api.grpc.external", "app.api.grpc.internal.object"],
    bindings={
        ObjectGrpcHandler:         add_ObjectServiceServicer_to_server,
        PermissionGrpcHandler:     add_PermissionServiceServicer_to_server,
        VersionGrpcHandler:        add_VersionServiceServicer_to_server,
        ObjectInternalGrpcHandler: add_ObjectInternalServiceServicer_to_server,
    },
)
