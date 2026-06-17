from datetime import datetime, timezone

from xime.core.transaction.manager import TransactionManager

from app.application.dto.reference.CreateObjectReferenceCommand import CreateObjectReferenceCommand
from app.application.dto.reference.CreateObjectReferenceResult import CreateObjectReferenceResult
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.reference.ObjectReferenceRepository import ObjectReferenceRepository
from app.application.service.audit.AuditService import AuditService
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.AppException import PublicError
from app.domain.audit.valueobject.AuditAction import AuditAction
from app.domain.object.model.ObjectReference import ObjectReference
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.object.valueobject.ResourceType import ResourceType
from app.domain.permission.capability.AclCapability import AclCapability
from app.domain.sharedkernel.factory.IdFactory import IdFactory


class CreateObjectReferenceUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        load_object: LoadObjectPort,
        reference_repository: ObjectReferenceRepository,
        authorization_service: AuthorizationService,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._load = load_object
        self._refs = reference_repository
        self._auth = authorization_service
        self._audit = audit_service

    async def execute(self, command: CreateObjectReferenceCommand) -> CreateObjectReferenceResult:
        now = datetime.now(timezone.utc)

        # A bad resource_type is client input → public 400.
        try:
            resource_type = ResourceType(command.resource_type)
        except ValueError as e:
            raise PublicError("E007001", str(e))

        async with self._tx():
            obj = await self._load.find_by_id(command.object_id)
            if obj is None or obj.status == ObjectStatus.PURGED:
                raise PublicError("E067000")

            await self._auth.require_capability(
                command.requester_identity_id, obj, AclCapability.WRITE
            )

            reference = ObjectReference(
                reference_id=IdFactory.generate(),
                object_id=command.object_id,
                application_identity_id=command.application_identity_id,
                application_name=command.application_name,
                resource_type=resource_type,
                resource_id=command.resource_id,
                created_at=now,
            )
            await self._refs.save(reference)

            await self._audit.record(
                command.object_id,
                command.requester_identity_id,
                command.requester_subject_type,
                command.requester_name,
                AuditAction.CREATE_REFERENCE,
            )

            return CreateObjectReferenceResult(reference_id=reference.reference_id)
