from xime.core.transaction.manager import TransactionManager

from app.application.dto.reference.DeleteObjectReferenceCommand import DeleteObjectReferenceCommand
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.reference.ObjectReferenceRepository import ObjectReferenceRepository
from app.application.service.audit.AuditService import AuditService
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.AppException import PublicError
from app.domain.audit.valueobject.AuditAction import AuditAction
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.capability.AclCapability import AclCapability


class DeleteObjectReferenceUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        load_object: LoadObjectPort,
        reference_repository: ObjectReferenceRepository,
        authorization_service: AuthorizationService,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._load = load_object
        self._refs = reference_repository
        self._auth = authorization_service
        self._audit = audit_service

    async def execute(self, command: DeleteObjectReferenceCommand) -> None:
        async with self._tx():
            obj = await self._load.find_by_id(command.object_id)
            if obj is None or obj.status == ObjectStatus.PURGED:
                raise PublicError("E067000")

            await self._auth.require_capability(
                command.requester_identity_id, obj, AclCapability.WRITE
            )

            reference = await self._refs.find_by_id(command.reference_id)
            # Must exist AND belong to this object (no cross-object delete).
            # Phải tồn tại VÀ thuộc đúng object này (không xóa chéo object).
            if reference is None or reference.object_id != command.object_id:
                raise PublicError("E067000")

            await self._refs.delete(command.reference_id)

            await self._audit.record(
                command.object_id,
                command.requester_identity_id,
                command.requester_subject_type,
                command.requester_name,
                AuditAction.DELETE_REFERENCE,
            )
