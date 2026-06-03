import logging
from datetime import datetime, timezone

from core.transaction.manager import TransactionManager

from app.application.dto.object.PurgeObjectCommand import PurgeObjectCommand
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.application.port.outbound.storage.BlobStoragePort import BlobStoragePort
from app.application.port.outbound.version.LoadVersionPort import LoadVersionPort
from app.application.service.audit.AuditService import AuditService
from app.common.constants.ObjectStatus import ObjectStatus
from app.common.exception.InvalidObjectStateException import InvalidObjectStateException
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.common.exception.PermissionDeniedException import PermissionDeniedException

_log = logging.getLogger(__name__)


class PurgeObjectUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        load_object: LoadObjectPort,
        save_object: SaveObjectPort,
        load_version: LoadVersionPort,
        blob_storage: BlobStoragePort,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._load = load_object
        self._save = save_object
        self._load_version = load_version
        self._blob = blob_storage
        self._audit = audit_service

    async def execute(self, command: PurgeObjectCommand) -> None:
        obj = await self._load.find_by_id(command.object_id)

        if obj is None or obj.status == ObjectStatus.PURGED:
            raise ObjectNotFoundException(command.object_id)

        # Only SOFT_DELETED can be purged
        if not obj.can_transition_to(ObjectStatus.PURGED):
            raise InvalidObjectStateException(obj.status.value, ObjectStatus.PURGED.value)

        # Only the owner can purge
        if obj.owner_identity_id != command.requester_identity_id:
            raise PermissionDeniedException()

        # Delete blobs for all versions — outside transaction (blob storage is not transactional)
        versions = await self._load_version.find_by_object(obj.object_id)
        for version in versions:
            try:
                await self._blob.delete(version.storage_pointer)
            except Exception:
                _log.warning(
                    "Failed to delete blob for version %s — pointer: %s",
                    version.version_id.hex(),
                    version.storage_pointer,
                )

        # Mark PURGED in DB — keep the row for audit trail
        now = datetime.now(timezone.utc)
        async with self._tx():
            purged = obj.purge(now)
            await self._save.update(purged)
            await self._audit.record(obj.object_id, command.requester_identity_id, "PURGE")
