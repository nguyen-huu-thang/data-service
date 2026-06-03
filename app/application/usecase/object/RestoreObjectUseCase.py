from datetime import datetime, timezone

from xime.core.transaction.manager import TransactionManager

from app.application.dto.object.RestoreObjectCommand import RestoreObjectCommand
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.application.service.audit.AuditService import AuditService
from app.common.constants.ObjectStatus import ObjectStatus
from app.common.exception.InvalidObjectStateException import InvalidObjectStateException
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.common.exception.PermissionDeniedException import PermissionDeniedException


class RestoreObjectUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        load_object: LoadObjectPort,
        save_object: SaveObjectPort,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._load = load_object
        self._save = save_object
        self._audit = audit_service

    async def execute(self, command: RestoreObjectCommand) -> None:
        now = datetime.now(timezone.utc)

        async with self._tx():
            obj = await self._load.find_by_id(command.object_id)

            if obj is None or obj.status == ObjectStatus.PURGED:
                raise ObjectNotFoundException(command.object_id)

            if not obj.can_transition_to(ObjectStatus.ACTIVE):
                raise InvalidObjectStateException(obj.status.value, ObjectStatus.ACTIVE.value)

            # Only the owner can restore
            if obj.owner_identity_id != command.requester_identity_id:
                raise PermissionDeniedException()

            restored = obj.restore(now)
            await self._save.update(restored)

            await self._audit.record(obj.object_id, command.requester_identity_id, "RESTORE")
