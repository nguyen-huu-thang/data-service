from xime.core.transaction.manager import TransactionManager

from app.application.dto.object.DownloadObjectQuery import DownloadObjectQuery
from app.application.dto.object.DownloadObjectResult import DownloadObjectResult
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.version.LoadVersionPort import LoadVersionPort
from app.application.service.audit.AuditService import AuditService
from app.domain.audit.valueobject.AuditAction import AuditAction
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.AppException import PublicError
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.capability.AclCapability import AclCapability


class DownloadObjectUseCase:
    """
    Download object content.

    Business flow:

    1. Load object metadata
    2. Ensure object exists and is not purged
    3. Verify requester has download permission
    4. Resolve content metadata (storage pointer + mime type)
    5. Write audit record
    6. Return the resolved location

    The blob bytes are intentionally NOT read here. The caller (REST adapter)
    streams them lazily from storage so large objects never buffer in memory;
    the gRPC adapter loads them to satisfy its unary contract.
    Cố ý KHÔNG đọc bytes ở đây. Bên gọi (adapter REST) stream lười từ storage nên
    object lớn không buffer vào RAM; adapter gRPC tải bytes để thỏa hợp đồng unary.
    """
    def __init__(
        self,
        transaction: TransactionManager,
        load_object: LoadObjectPort,
        load_version: LoadVersionPort,
        authorization_service: AuthorizationService,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._load = load_object
        self._load_version = load_version
        self._auth = authorization_service
        self._audit = audit_service

    async def execute(self, query: DownloadObjectQuery) -> DownloadObjectResult:
        storage_pointer: str
        mime_type = "application/octet-stream"

        async with self._tx():
            obj = await self._load.find_by_id(query.object_id)

            if obj is None or obj.status == ObjectStatus.PURGED:
                raise PublicError("E067000")

            await self._auth.require_capability(
                query.requester_identity_id,
                obj,
                AclCapability.DOWNLOAD,
            )

            storage_pointer = obj.storage_pointer

            if obj.current_version_id:
                version = await self._load_version.find_by_id(obj.current_version_id)
                if version:
                    mime_type = version.mime_type.value

            await self._audit.record(
                query.object_id,
                query.requester_identity_id,
                query.requester_subject_type,
                query.requester_name,
                AuditAction.DOWNLOAD,
            )

        return DownloadObjectResult(
            storage_pointer=storage_pointer,
            mime_type=mime_type,
        )
