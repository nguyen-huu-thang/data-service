import logging
from datetime import datetime, timezone

from xime.core.transaction.manager import TransactionManager

from app.application.dto.object.PurgeObjectCommand import PurgeObjectCommand
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.application.port.outbound.storage.BlobStoragePort import BlobStoragePort
from app.application.port.outbound.version.LoadVersionPort import LoadVersionPort
from app.application.service.audit.AuditService import AuditService
from app.common.exception.InvalidObjectStateException import InvalidObjectStateException
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.common.exception.PermissionDeniedException import PermissionDeniedException
from app.domain.object.valueobject.ObjectStatus import ObjectStatus

_log = logging.getLogger(__name__)


class PurgeObjectUseCase:
    """
    Permanently remove object content.

    Business flow:

    1. Load object
    2. Ensure object exists and is not already purged
    3. Validate state transition -> PURGED
    4. Verify requester is owner
    5. Delete blobs for all versions
    6. Mark object as PURGED
    7. Write audit record

    Purge is irreversible.

    Database records are intentionally preserved after purge
    for auditability and historical tracking.
    """

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

        now = datetime.now(timezone.utc)

        # Lock, validate, delete blobs and persist within a single transaction
        # so two concurrent purges cannot both pass the checks and produce
        # duplicate work / audit records. The lock on the object row serializes
        # purges per object.
        async with self._tx():

            # Load + lock current object state.
            obj = await self._load.find_by_id_for_update(command.object_id)

            # Purged objects are treated as non-existent.
            if obj is None or obj.status == ObjectStatus.PURGED:
                raise ObjectNotFoundException(command.object_id)

            # Purge is intentionally restricted to the owner.
            #
            # Authorize before validating lifecycle state: unlike
            # READ/WRITE/DELETE, purge bypasses ACL and requires direct
            # ownership because it permanently destroys stored content.
            # Checking ownership first avoids leaking object state to callers
            # who have no right to purge it.
            if obj.owner_identity_id != command.requester_identity_id:
                raise PermissionDeniedException()

            # Purge is only allowed after soft deletion.
            #
            # Expected lifecycle:
            #
            # ACTIVE
            #   -> SOFT_DELETED
            #   -> PURGED
            #
            # This prevents accidental permanent deletion.
            if not obj.can_transition_to(ObjectStatus.PURGED):
                raise InvalidObjectStateException(
                    obj.status.value,
                    ObjectStatus.PURGED.value,
                )

            # Blob storage cannot participate in a database transaction.
            #
            # Delete all version content. Failure to remove a blob should not
            # stop the purge process; orphaned content can be handled later by
            # maintenance jobs.
            versions = await self._load_version.find_by_object(
                obj.object_id
            )

            for version in versions:
                try:
                    await self._blob.delete(
                        version.storage_pointer
                    )
                except Exception:
                    _log.warning(
                        "Failed to delete blob for version %s — pointer: %s",
                        version.version_id.hex(),
                        version.storage_pointer,
                    )

            # Domain model controls purge state transition.
            purged = obj.purge(now)

            # Keep metadata row for auditing — only content is physically removed.
            await self._save.update(purged)

            # Record irreversible purge action.
            await self._audit.record(
                obj.object_id,
                command.requester_identity_id,
                command.requester_subject_type,
                command.requester_name,
                "PURGE",
            )