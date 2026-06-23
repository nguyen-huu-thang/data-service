from app.application.dto.version.DownloadVersionQuery import DownloadVersionQuery
from app.application.dto.version.DownloadVersionResult import DownloadVersionResult
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.version.LoadVersionPort import LoadVersionPort
from app.application.service.audit.AuditService import AuditService
from app.domain.audit.valueobject.AuditAction import AuditAction
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.AppException import PublicError
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.capability.AclCapability import AclCapability


class DownloadVersionUseCase:
    def __init__(
        self,
        load_object: LoadObjectPort,
        load_version: LoadVersionPort,
        authorization_service: AuthorizationService,
        audit_service: AuditService,
    ) -> None:
        self._load = load_object
        self._load_version = load_version
        self._auth = authorization_service
        self._audit = audit_service

    async def execute(self, query: DownloadVersionQuery) -> DownloadVersionResult:
        obj = await self._load.find_by_id(query.object_id)

        if obj is None or obj.status == ObjectStatus.PURGED:
            raise PublicError("E067000")

        await self._auth.require_capability(
            query.requester_identity_id, obj, AclCapability.DOWNLOAD
        )

        version = await self._load_version.find_by_id(query.version_id)

        if version is None or version.object_id != query.object_id:
            raise PublicError("E067000")

        await self._audit.record(
            query.object_id,
            query.requester_identity_id,
            query.requester_subject_type,
            query.requester_name,
            AuditAction.DOWNLOAD_VERSION,
        )

        # Blob bytes are NOT read here — the adapter streams/loads them from the
        # resolved pointer. Keeps large versions out of memory in the use case.
        # KHÔNG đọc bytes ở đây - adapter stream/tải từ pointer đã phân giải.
        return DownloadVersionResult(
            storage_pointer=version.storage_pointer,
            mime_type=version.mime_type.value,
            content_hash=version.content_hash.value,
            version_number=version.version_number,
        )
