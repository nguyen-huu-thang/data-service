from datetime import datetime, timezone

from xime.core.transaction.manager import TransactionManager

from app.application.dto.object.ArchiveObjectCommand import ArchiveObjectCommand
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.application.service.audit.AuditService import AuditService
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.AppException import PublicError
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.capability.AclCapability import AclCapability


class ArchiveObjectUseCase:
    """
    Archive an existing object.

    Business flow:

    1. Load object
    2. Ensure object exists and is not purged
    3. Validate state transition -> ARCHIVED
    4. Verify requester has DELETE capability
    5. Archive object
    6. Persist changes
    7. Write audit record

    All operations execute inside a single transaction.
    """

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
        # Timestamp used for archive metadata.
        now = datetime.now(timezone.utc)

        # Object update and audit logging must succeed or fail together.
        async with self._tx():

            # Load current object state.
            obj = await self._load.find_by_id(command.object_id)

            # Purged objects are treated as non-existent.
            if obj is None or obj.status == ObjectStatus.PURGED:
                raise PublicError("E067000")

            # Archive is considered a delete-like operation.
            #
            # Authorize before validating the state transition so an
            # unauthorized caller cannot probe the object's current status.
            #
            # AuthorizationService grants access when:
            # - requester has DATA_DELETE_ANY system permission
            # - requester is object owner
            # - requester has DELETE capability in object ACL
            await self._auth.require_capability(
                command.requester_identity_id,
                obj,
                AclCapability.DELETE,
            )

            # Domain state machine validation.
            # Example:
            # ACTIVE   -> ARCHIVED   (allowed)
            # PURGED   -> ARCHIVED   (not allowed)
            if not obj.can_transition_to(ObjectStatus.ARCHIVED):
                raise PublicError("E067002")

            # Delegate state transition to domain model.
            # Domain object decides how archive metadata is produced.
            archived = obj.archive(now)

            # Persist archived state.
            await self._save.update(archived)

            # Record immutable audit trail.
            await self._audit.record(
                obj.object_id,
                command.requester_identity_id,
                command.requester_subject_type,
                command.requester_name,
                "ARCHIVE",
            )