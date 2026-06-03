from xime.core.config.binding import BindingConfig
from xime.core.transaction.manager import TransactionManager
from xime.starters.sqlalchemy import SqlAlchemyTransactionManager

from app.api.grpc.mapper.ObjectGrpcMapper import ObjectGrpcMapper
from app.api.grpc.mapper.VersionGrpcMapper import VersionGrpcMapper
from app.application.port.outbound.audit.SaveAuditPort import SaveAuditPort
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.application.port.outbound.permission.LoadPermissionPort import LoadPermissionPort
from app.application.port.outbound.permission.SavePermissionPort import SavePermissionPort
from app.application.port.outbound.storage.BlobStoragePort import BlobStoragePort
from app.application.port.outbound.version.LoadVersionPort import LoadVersionPort
from app.application.port.outbound.version.SaveVersionPort import SaveVersionPort
from app.infrastructure.persistence.repository.audit.SqlAlchemyAuditRepository import SqlAlchemyAuditRepository
from app.infrastructure.persistence.repository.object.SqlAlchemyObjectRepository import SqlAlchemyObjectRepository
from app.infrastructure.persistence.repository.permission.SqlAlchemyPermissionRepository import SqlAlchemyPermissionRepository
from app.infrastructure.persistence.repository.version.SqlAlchemyVersionRepository import SqlAlchemyVersionRepository
from app.infrastructure.storage.minio.MinioStorageAdapter import MinioStorageAdapter

# ── DI configuration for Data Service ────────────────────────────────────────
#
# Framework reads the `dependency` variable from this module at startup.
# Rule: all scanned classes must have fully type-hinted constructors.
#
# Excluded by default (scanner skips segments):
#   domain, dto, entity, vo, constant, exception
# ─────────────────────────────────────────────────────────────────────────────

dependency = BindingConfig()

# ── Manual registration — classes outside auto-scan ───────────────────────────
# app.api.grpc.mapper is not scanned; register mappers explicitly so they can
# be injected into handlers instead of being instantiated manually.

dependency.register(
    ObjectGrpcMapper,
    VersionGrpcMapper,
)

# ── Package scan ──────────────────────────────────────────────────────────────

dependency.scan(
    # Framework starters (uses __all__ to register only DI-managed singletons)
    "starters.sqlalchemy",
    # Application services
    "app.application.service",
    # Core use cases (object CRUD + lifecycle)
    "app.application.usecase.object",
    # Version use cases (Phase 11)
    "app.application.usecase.version",
    # Infrastructure — DB repositories
    "app.infrastructure.persistence.repository",
    # Infrastructure — blob storage
    "app.infrastructure.storage",
    # Integration — Trust Service key sync
    "app.integration.trust.key",
    # API — gRPC handlers (external + internal)
    "app.api.grpc.external",
    "app.api.grpc.internal.object",
)

# ── Protocol → Implementation bindings ───────────────────────────────────────

dependency.bind({
    # Transaction
    TransactionManager:    SqlAlchemyTransactionManager,
    # Object
    LoadObjectPort:        SqlAlchemyObjectRepository,
    SaveObjectPort:        SqlAlchemyObjectRepository,
    # Permission
    LoadPermissionPort:    SqlAlchemyPermissionRepository,
    SavePermissionPort:    SqlAlchemyPermissionRepository,
    # Version
    LoadVersionPort:       SqlAlchemyVersionRepository,
    SaveVersionPort:       SqlAlchemyVersionRepository,
    # Blob storage
    BlobStoragePort:       MinioStorageAdapter,
    # Audit
    SaveAuditPort:         SqlAlchemyAuditRepository,
})
