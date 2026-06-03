from datetime import datetime, timezone

from xime.core.transaction.manager import TransactionManager

from app.application.dto.object.DeleteObjectCommand import DeleteObjectCommand
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.application.service.audit.AuditService import AuditService
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.constants.Capability import Capability
from app.common.exception.ObjectAlreadyDeletedException import ObjectAlreadyDeletedException
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException


class DeleteObjectUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        load_object: LoadObjectPort,
        save_object: SaveObjectPort,
        authorization_service: AuthorizationService,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._load = load_object
        self._save = save_object
        self._auth = authorization_service
        self._audit = audit_service

    async def execute(self, command: DeleteObjectCommand) -> None:
        now = datetime.now(timezone.utc)

        async with self._tx():
            obj = await self._load.find_by_id(command.object_id)

            if obj is None or obj.status.value == "PURGED":
                raise ObjectNotFoundException(command.object_id)

            if obj.is_deleted():
                raise ObjectAlreadyDeletedException(command.object_id)

            await self._auth.require_capability(
                command.requester_identity_id,
                obj,
                Capability.DELETE,
            )

            deleted = obj.soft_delete(now)
            await self._save.update(deleted)

            await self._audit.record(obj.object_id, command.requester_identity_id, "DELETE")
