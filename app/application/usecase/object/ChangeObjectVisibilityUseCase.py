from datetime import datetime, timezone

from xime.core.transaction.manager import TransactionManager

from app.application.dto.object.ChangeObjectVisibilityCommand import ChangeObjectVisibilityCommand
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.application.service.audit.AuditService import AuditService
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.capability.AclCapability import AclCapability


class ChangeObjectVisibilityUseCase:
    """
    Change object visibility (PUBLIC / PRIVATE / ...).

    Business flow:

    1. Load object
    2. Ensure object exists and is not purged
    3. Verify requester can modify object settings
    4. Change visibility through domain model
    5. Persist updated state
    6. Write audit record

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

    async def execute(self, command: ChangeObjectVisibilityCommand) -> None:
        # Timestamp used by the domain model when applying visibility changes.
        now = datetime.now(timezone.utc)

        # Object update and audit logging must succeed or fail together.
        async with self._tx():

            # Load current object state.
            obj = await self._load.find_by_id(command.object_id)

            # Purged objects are treated as non-existent.
            if obj is None or obj.status == ObjectStatus.PURGED:
                raise ObjectNotFoundException(command.object_id)

            # Visibility is considered a modification of object metadata.
            #
            # AuthorizationService grants access when:
            # - requester has DATA_WRITE_ANY system permission
            # - requester is object owner
            # - requester has WRITE capability in object ACL
            await self._auth.require_capability(
                command.requester_identity_id,
                obj,
                AclCapability.WRITE,
            )

            # Delegate visibility rules to the domain model.
            #
            # The domain object decides:
            # - whether the requested visibility is valid
            # - which fields must be updated
            # - how timestamps are applied
            updated = obj.change_visibility(
                command.visibility,
                now,
            )

            # Persist updated object state.
            await self._save.update(updated)

            # Record immutable audit trail for visibility changes.
            await self._audit.record(
                obj.object_id,
                command.requester_identity_id,
                command.requester_subject_type,
                command.requester_name,
                "CHANGE_VISIBILITY",
            )