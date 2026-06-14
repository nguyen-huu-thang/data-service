from xime.adapters.web import configure_controllers, configure_exception_handlers
from xime.adapters.web.openapi import JwtBearer, OpenApiConfig, configure_openapi

from app.api.rest.error_handler import app_exception_handler, unhandled_exception_handler
from app.common.exception.AppException import AppException

configure_controllers(
    "app.api.rest.external.object",
    "app.api.rest.external.version",
)

# Platform error standard: AppException renders {errorKey, code, message} with
# per-channel redaction; the catch-all guarantees no raw exception ever leaks.
# Chuẩn mã lỗi platform: AppException trả {errorKey, code, message} có che theo
# kênh; handler catch-all đảm bảo không exception thô nào lọt ra ngoài.
configure_exception_handlers(
    {
        AppException: app_exception_handler,
        Exception: unhandled_exception_handler,
    }
)

configure_openapi(
    OpenApiConfig(
        title="Data Service",
        version="1.0.0",
        description=(
            "**Data Service** — distributed data infrastructure của Base Platform (Xime ecosystem).\n\n"
            "Chịu trách nhiệm:\n"
            "- Object storage và quản lý vòng đời dữ liệu\n"
            "- Phân quyền theo capability (READ, WRITE, DELETE, SHARE, DOWNLOAD)\n"
            "- Versioning cho mọi loại data object\n"
            "- Định tuyến theo shard dựa trên `owner_identity_id`\n\n"
            "Tất cả endpoint yêu cầu `Authorization: Bearer <JWT>`."
        ),
        security=JwtBearer(),
        public_paths=[],
        swagger_ui_title="Data Service - Swagger UI",
    )
)
