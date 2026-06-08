from datetime import datetime, timezone

from xime.core.transaction.manager import TransactionManager

from app.application.dto.object.ArchiveObjectCommand import ArchiveObjectCommand
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.application.service.audit.AuditService import AuditService
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.InvalidObjectStateException import InvalidObjectStateException
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.capability.AclCapability import AclCapability


class ArchiveObjectUseCase:
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

    async def execute(self, command: ArchiveObjectCommand) -> None:
        now = datetime.now(timezone.utc)

        async with self._tx():
            obj = await self._load.find_by_id(command.object_id)

            if obj is None or obj.status == ObjectStatus.PURGED:
                raise ObjectNotFoundException(command.object_id)

            if not obj.can_transition_to(ObjectStatus.ARCHIVED):
                raise InvalidObjectStateException(obj.status.value, ObjectStatus.ARCHIVED.value)

            await self._auth.require_capability(
                command.requester_identity_id, obj, AclCapability.DELETE
            )

            archived = obj.archive(now)
            await self._save.update(archived)

            await self._audit.record(
                obj.object_id,
                command.requester_identity_id,
                command.requester_subject_type,
                command.requester_name,
                "ARCHIVE",
            )
