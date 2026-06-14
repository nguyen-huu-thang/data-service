from datetime import datetime, timezone

from xime.core.transaction.manager import TransactionManager

from app.application.dto.permission.RevokeObjectPermissionCommand import RevokeObjectPermissionCommand
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.application.port.outbound.permission.LoadPermissionPort import LoadPermissionPort
from app.application.port.outbound.permission.SavePermissionPort import SavePermissionPort
from app.application.service.audit.AuditService import AuditService
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.AppException import PublicError
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.capability.AclCapability import AclCapability


class RevokeObjectPermissionUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        load_object: LoadObjectPort,
        save_object: SaveObjectPort,
        load_permission: LoadPermissionPort,
        save_permission: SavePermissionPort,
        authorization_service: AuthorizationService,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._load = load_object
        self._save = save_object
        self._load_permission = load_permission
        self._save_permission = save_permission
        self._auth = authorization_service
        self._audit = audit_service

    async def execute(self, command: RevokeObjectPermissionCommand) -> None:
        now = datetime.now(timezone.utc)

        async with self._tx():
            obj = await self._load.find_by_id(command.object_id)

            if obj is None or obj.status == ObjectStatus.PURGED:
                raise PublicError("E067000")

            await self._auth.require_capability(
                command.requester_identity_id, obj, AclCapability.SHARE
            )

            existing = await self._load_permission.find_by_subject_and_object(
                subject_identity_id=command.target_identity_id,
                object_id=command.object_id,
            )
            if existing is not None:
                await self._save_permission.delete(existing.permission_id)

                updated_obj = obj.increase_permission_version(now)
                await self._save.update(updated_obj)

            await self._audit.record(
                obj.object_id,
                command.requester_identity_id,
                command.requester_subject_type,
                command.requester_name,
                "REVOKE_PERMISSION",
            )
