from app.application.dto.audit.ListObjectAuditQuery import ListObjectAuditQuery
from app.application.port.outbound.audit.LoadAuditPort import LoadAuditPort
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.AppException import PublicError
from app.domain.audit.model.ObjectAudit import ObjectAudit
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.capability.AclCapability import AclCapability


class ListObjectAuditUseCase:
    """
    Read the audit trail of an object. Only callers who can READ the object may
    view its audit history.

    Đọc vết audit của một object. Chỉ caller có quyền READ object mới xem được
    lịch sử audit.
    """

    def __init__(
        self,
        load_object: LoadObjectPort,
        load_audit: LoadAuditPort,
        authorization_service: AuthorizationService,
    ) -> None:
        self._load = load_object
        self._load_audit = load_audit
        self._auth = authorization_service

    async def execute(self, query: ListObjectAuditQuery) -> list[ObjectAudit]:
        obj = await self._load.find_by_id(query.object_id)

        if obj is None or obj.status == ObjectStatus.PURGED:
            raise PublicError("E067000")

        await self._auth.require_capability(
            query.requester_identity_id, obj, AclCapability.READ
        )

        return await self._load_audit.find_by_object(query.object_id)
