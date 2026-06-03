from xime.adapters.web.openapi import JwtBearer, OpenApiConfig, configure_openapi

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
    )
)
