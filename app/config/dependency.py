from xime.core.config.binding import BindingConfig
from xime.core.transaction.manager import TransactionManager
from xime.starters.sqlalchemy import SqlAlchemyTransactionManager

from app.api.grpc.mapper.ObjectGrpcMapper import ObjectGrpcMapper
from app.api.grpc.mapper.VersionGrpcMapper import VersionGrpcMapper

# Structured ports (hexagonal architecture)
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.application.port.outbound.version.LoadVersionPort import LoadVersionPort
from app.application.port.outbound.version.SaveVersionPort import SaveVersionPort
from app.application.port.outbound.permission.LoadPermissionPort import LoadPermissionPort
from app.application.port.outbound.permission.SavePermissionPort import SavePermissionPort
from app.application.port.outbound.permission.LoadSubjectPermissionPort import LoadSubjectPermissionPort
from app.application.port.outbound.audit.SaveAuditPort import SaveAuditPort
from app.application.port.outbound.audit.LoadAuditPort import LoadAuditPort
from app.application.port.outbound.storage.BlobStoragePort import BlobStoragePort

# Trust ports
from app.application.port.outbound.trust.LoadCertificatePort import LoadCertificatePort
from app.application.port.outbound.trust.SaveCertificatePort import SaveCertificatePort
from app.application.port.outbound.trust.LoadVerificationKeyPort import LoadVerificationKeyPort
from app.application.port.outbound.trust.SaveVerificationKeyPort import SaveVerificationKeyPort

# Subject ports
from app.application.port.outbound.subject.SubjectInfoRepository import SubjectInfoRepository
from app.application.port.outbound.permission.SubjectPermissionRepository import SubjectPermissionRepository

# Share / tag / reference ports
from app.application.port.outbound.reference.ObjectReferenceRepository import ObjectReferenceRepository
from app.application.port.outbound.share.ObjectShareRepository import ObjectShareRepository
from app.application.port.outbound.tag.ObjectTagRepository import ObjectTagRepository

from app.infrastructure.storage.local.LocalDiskStorageAdapter import LocalDiskStorageAdapter

# Trust repositories
from app.infrastructure.persistence.repository.trust.TrustCertificateRepository import TrustCertificateRepository
from app.infrastructure.persistence.repository.trust.TrustVerificationKeyRepository import TrustVerificationKeyRepository

# Manually registered trust classes (not in scanned packages)
from app.integration.trust.bootstrap.Bootstrap import Bootstrap

# Domain services/policies (domain package is excluded from auto-scan)
from app.domain.permission.policy.AccessPolicy import AccessPolicy
from app.domain.sharedkernel.routing.ShardRouter import ShardRouter

# Structured repositories
from app.infrastructure.persistence.repository.object.SqlAlchemyObjectRepository import (
    SqlAlchemyObjectRepository as StructuredObjectRepository,
)
from app.infrastructure.persistence.repository.permission.SqlAlchemyPermissionRepository import (
    SqlAlchemyPermissionRepository as StructuredPermissionRepository,
)
from app.infrastructure.persistence.repository.version.SqlAlchemyVersionRepository import (
    SqlAlchemyVersionRepository as StructuredVersionRepository,
)
from app.infrastructure.persistence.repository.audit.SqlAlchemyAuditRepository import (
    SqlAlchemyAuditRepository as StructuredAuditRepository,
)
from app.infrastructure.persistence.repository.subject.SqlAlchemySubjectInfoRepository import SqlAlchemySubjectInfoRepository
from app.infrastructure.persistence.repository.permission.SqlAlchemySubjectPermissionRepository import SqlAlchemySubjectPermissionRepository

# Share / tag / reference repositories
from app.infrastructure.persistence.repository.reference.SqlAlchemyObjectReferenceRepository import SqlAlchemyObjectReferenceRepository
from app.infrastructure.persistence.repository.share.SqlAlchemyObjectShareRepository import SqlAlchemyObjectShareRepository
from app.infrastructure.persistence.repository.tag.SqlAlchemyObjectTagRepository import SqlAlchemyObjectTagRepository


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
    # Bootstrap creates BootstrapLoader/BootstrapValidator internally,
    # so they're not DI-managed — only Bootstrap itself is registered here.
    Bootstrap,
    # Domain services/policies — pure, no dependencies; injected into app services.
    # Dịch vụ/policy domain - thuần, không phụ thuộc; inject vào service application.
    AccessPolicy,
    ShardRouter,
)

# ── Package scan ──────────────────────────────────────────────────────────────

dependency.scan(
    # Framework starters (uses __all__ to register only DI-managed singletons)
    "xime.starters.sqlalchemy",
    # Application services
    "app.application.service",
    # Core use cases (object CRUD + lifecycle)
    "app.application.usecase.object",
    # Version use cases
    "app.application.usecase.version",
    # Permission use cases
    "app.application.usecase.permission",
    # Subject sync use cases
    "app.application.usecase.subject",
    # Audit read use cases
    "app.application.usecase.audit",
    # Share / tag / reference use cases
    "app.application.usecase.share",
    "app.application.usecase.tag",
    "app.application.usecase.reference",
    # Infrastructure — DB repositories (structured)
    "app.infrastructure.persistence.repository.object",
    "app.infrastructure.persistence.repository.permission",
    "app.infrastructure.persistence.repository.version",
    "app.infrastructure.persistence.repository.audit",
    "app.infrastructure.persistence.repository.subject",
    "app.infrastructure.persistence.repository.share",
    "app.infrastructure.persistence.repository.tag",
    "app.infrastructure.persistence.repository.reference",
    # Infrastructure — blob storage
    "app.infrastructure.storage",
    # Infrastructure — Trust repositories
    "app.infrastructure.persistence.repository.trust",
    # Integration — Trust Service (all sub-packages)
    "app.integration.trust.publicca",
    "app.integration.trust.certificate",
    "app.integration.trust.ssl",
    "app.integration.trust.key",
    "app.integration.trust.startup",
    "app.integration.trust.scheduler",
    # API — gRPC mappers
    "app.api.grpc.mapper",
    # API — gRPC handlers (external + internal)
    "app.api.grpc.external",
    "app.api.grpc.internal.object",
    # API — REST controllers
    "app.api.rest.external.object",
    "app.api.rest.external.version",
    "app.api.rest.external.share",
    "app.api.rest.external.tag",
    "app.api.rest.external.reference",
    # API — REST mappers
    "app.api.rest.mapper",
)

# ── Protocol → Implementation bindings ───────────────────────────────────────

dependency.bind({
    # Transaction
    TransactionManager: SqlAlchemyTransactionManager,

    # Structured ports → structured repositories
    LoadObjectPort: StructuredObjectRepository,
    SaveObjectPort: StructuredObjectRepository,

    LoadVersionPort: StructuredVersionRepository,
    SaveVersionPort: StructuredVersionRepository,

    LoadPermissionPort: StructuredPermissionRepository,
    SavePermissionPort: StructuredPermissionRepository,

    LoadSubjectPermissionPort: SqlAlchemySubjectPermissionRepository,

    SaveAuditPort: StructuredAuditRepository,
    LoadAuditPort: StructuredAuditRepository,

    # Blob storage
    BlobStoragePort: LocalDiskStorageAdapter,

    # Trust ports → Trust repositories
    LoadCertificatePort: TrustCertificateRepository,
    SaveCertificatePort: TrustCertificateRepository,
    LoadVerificationKeyPort: TrustVerificationKeyRepository,
    SaveVerificationKeyPort: TrustVerificationKeyRepository,

    # Subject ports → subject repositories
    SubjectPermissionRepository: SqlAlchemySubjectPermissionRepository,
    SubjectInfoRepository: SqlAlchemySubjectInfoRepository,

    # Share / tag / reference ports → repositories
    ObjectReferenceRepository: SqlAlchemyObjectReferenceRepository,
    ObjectShareRepository: SqlAlchemyObjectShareRepository,
    ObjectTagRepository: SqlAlchemyObjectTagRepository,
})
