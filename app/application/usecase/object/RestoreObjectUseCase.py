from datetime import datetime, timezone

from xime.core.transaction.manager import TransactionManager

from app.application.dto.object.RestoreObjectCommand import RestoreObjectCommand
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.application.service.audit.AuditService import AuditService
from app.common.exception.InvalidObjectStateException import InvalidObjectStateException
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.common.exception.PermissionDeniedException import PermissionDeniedException
from app.domain.object.valueobject.ObjectStatus import ObjectStatus


class RestoreObjectUseCase:
    """
    Restore a soft-deleted object.

    Business flow:

    1. Load object
    2. Ensure object exists and is not purged
    3. Validate state transition -> ACTIVE
    4. Verify requester is owner
    5. Restore object
    6. Persist updated state
    7. Write audit record

    Soft-deleted and archived objects can be restored to ACTIVE.
    Purged objects cannot be recovered.
    """

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

        # Timestamp used for restore metadata.
        now = datetime.now(timezone.utc)

        # Object update and audit logging must succeed or fail together.
        async with self._tx():

            # Load current object state.
            obj = await self._load.find_by_id(command.object_id)

            # Purged objects are considered permanently removed.
            #
            # Restore is only supported for soft-deleted objects.
            if obj is None or obj.status == ObjectStatus.PURGED:
                raise ObjectNotFoundException(command.object_id)

            # Restore is intentionally restricted to the owner.
            #
            # Ownership is required because restore may make previously hidden
            # content available again. Authorize before validating the state
            # transition so an unauthorized caller cannot probe the object's
            # current status.
            if obj.owner_identity_id != command.requester_identity_id:
                raise PermissionDeniedException()

            # Validate lifecycle transition.
            #
            # Expected transitions:
            #
            # SOFT_DELETED -> ACTIVE
            # ARCHIVED     -> ACTIVE
            #
            # Other states are rejected by the domain model.
            if not obj.can_transition_to(ObjectStatus.ACTIVE):
                raise InvalidObjectStateException(
                    obj.status.value,
                    ObjectStatus.ACTIVE.value,
                )

            # Delegate restore rules to the domain model.
            restored = obj.restore(now)

            # Persist updated state.
            await self._save.update(restored)

            # Record restoration activity.
            await self._audit.record(
                obj.object_id,
                command.requester_identity_id,
                command.requester_subject_type,
                command.requester_name,
                "RESTORE",
            )