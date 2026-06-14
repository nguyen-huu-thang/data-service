from xime.adapters.grpc import configure_grpc_clients, configure_grpc_services, configure_grpc_tls

from clients.trust import KeyDistributionServiceClient
from app.integration.trust.ssl.TrustGrpcCertificateProvider import TrustGrpcCertificateProvider
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

# Dynamic mTLS: certs come from the Trust-synchronized resolvers, re-read on
# every new TLS handshake (rotation without restart). On/off stays in
# application.yml (grpc.tls.enabled).
# mTLS động: cert lấy từ resolver đồng bộ với Trust, đọc lại ở mỗi handshake
# mới (rotate không cần restart). Bật/tắt vẫn nằm ở application.yml.
configure_grpc_tls(provider=TrustGrpcCertificateProvider)

# Outbound gRPC client to Trust. The framework builds a managed XimeGrpcChannel
# from grpc.clients.trust in application.yml (host/port/deadline + dynamic mTLS)
# and registers the SDK client instance in DI so TrustKeyClient can inject it.
# Client gRPC ra Trust. Framework dựng XimeGrpcChannel có quản lý từ
# grpc.clients.trust trong application.yml (host/port/deadline + mTLS động) và
# đăng ký instance client SDK vào DI để TrustKeyClient inject được.
configure_grpc_clients("trust", KeyDistributionServiceClient)
