from datetime import datetime, timezone

from xime.core.transaction.manager import TransactionManager

from app.application.dto.object.DeleteObjectCommand import DeleteObjectCommand
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.application.service.audit.AuditService import AuditService
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.AppException import PublicError
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.capability.AclCapability import AclCapability


class DeleteObjectUseCase:
    """
    Soft-delete an existing object.

    Business flow:

    1. Load object
    2. Ensure object exists and is not purged
    3. Ensure object is not already deleted
    4. Verify requester has delete permission
    5. Mark object as deleted
    6. Persist updated state
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

    async def execute(self, command: DeleteObjectCommand) -> None:
        # Timestamp used for deletion metadata.
        now = datetime.now(timezone.utc)

        # Object update and audit logging must succeed or fail together.
        async with self._tx():

            # Load current object state.
            obj = await self._load.find_by_id(command.object_id)

            # Purged objects are treated as non-existent.
            if obj is None or obj.status == ObjectStatus.PURGED:
                raise PublicError("E067000")

            # Delete permission is required.
            #
            # Authorize before inspecting the object's deleted state so an
            # unauthorized caller cannot distinguish "already deleted" from
            # "no permission".
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

            # Prevent duplicate delete operations.
            #
            # DELETE is expected to transition an ACTIVE object into a
            # deleted state. Repeating the operation is considered an
            # application error rather than a no-op.
            if obj.is_deleted():
                raise PublicError("E067001")

            # Delegate deletion rules to the domain model.
            #
            # Domain object decides how deletion metadata and state
            # transitions are applied.
            deleted = obj.soft_delete(now)

            # Persist updated object state.
            await self._save.update(deleted)

            # Record immutable audit trail.
            await self._audit.record(
                obj.object_id,
                command.requester_identity_id,
                command.requester_subject_type,
                command.requester_name,
                "DELETE",
            )