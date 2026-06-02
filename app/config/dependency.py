from core.config.binding import BindingConfig
from core.transaction.manager import TransactionManager
from starters.sqlalchemy import SqlAlchemyTransactionManager

from app.application.port.outbound.audit.SaveAuditPort import SaveAuditPort
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.application.port.outbound.permission.LoadPermissionPort import LoadPermissionPort
from app.application.port.outbound.permission.SavePermissionPort import SavePermissionPort
from app.application.port.outbound.storage.BlobStoragePort import BlobStoragePort
from app.application.port.outbound.version.LoadVersionPort import LoadVersionPort
from app.application.port.outbound.version.SaveVersionPort import SaveVersionPort
from app.infrastructure.persistence.repository.audit.NoopAuditRepository import NoopAuditRepository
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

# ── Package scan ──────────────────────────────────────────────────────────────

dependency.scan(
    # Framework starters (uses __all__ to register only DI-managed singletons)
    "starters.sqlalchemy",
    # Application services
    "app.application.service",
    # Core use cases (object CRUD)
    "app.application.usecase.object",
    # Infrastructure — DB repositories
    "app.infrastructure.persistence.repository",
    # Infrastructure — blob storage
    "app.infrastructure.storage",
    # Integration — Trust Service key sync
    "app.integration.trust.key",
    # API — gRPC handlers
    "app.api.grpc.external",
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
    # Audit (NoopAuditRepository until Phase 12 replaces it)
    SaveAuditPort:         NoopAuditRepository,
})
