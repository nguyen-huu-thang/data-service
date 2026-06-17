from xime.core.transaction.manager import TransactionManager

from app.application.dto.share.RevokeObjectShareCommand import RevokeObjectShareCommand
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.share.ObjectShareRepository import ObjectShareRepository
from app.application.service.audit.AuditService import AuditService
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.AppException import PublicError
from app.domain.audit.valueobject.AuditAction import AuditAction
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.capability.AclCapability import AclCapability


class RevokeObjectShareUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        load_object: LoadObjectPort,
        share_repository: ObjectShareRepository,
        authorization_service: AuthorizationService,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._load = load_object
        self._share = share_repository
        self._auth = authorization_service
        self._audit = audit_service

    async def execute(self, command: RevokeObjectShareCommand) -> None:
        async with self._tx():
            obj = await self._load.find_by_id(command.object_id)
            if obj is None or obj.status == ObjectStatus.PURGED:
                raise PublicError("E067000")

            await self._auth.require_capability(
                command.requester_identity_id, obj, AclCapability.SHARE
            )

            share = await self._share.find_by_id(command.share_id)
            # The share must exist AND belong to this object (no cross-object revoke).
            # Share phải tồn tại VÀ thuộc đúng object này (không revoke chéo object).
            if share is None or share.object_id != command.object_id:
                raise PublicError("E067000")

            await self._share.delete(command.share_id)

            await self._audit.record(
                command.object_id,
                command.requester_identity_id,
                command.requester_subject_type,
                command.requester_name,
                AuditAction.REVOKE_SHARE,
            )
