from xime.core.transaction.manager import TransactionManager

from app.application.dto.object.GetObjectQuery import GetObjectQuery
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.service.audit.AuditService import AuditService
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.domain.object.model.DataObject import DataObject
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.capability.AclCapability import AclCapability


class GetObjectUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        load_object: LoadObjectPort,
        authorization_service: AuthorizationService,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._load = load_object
        self._auth = authorization_service
        self._audit = audit_service

    async def execute(self, query: GetObjectQuery) -> DataObject:
        async with self._tx():
            obj = await self._load.find_by_id(query.object_id)

            if obj is None or obj.status == ObjectStatus.PURGED:
                raise ObjectNotFoundException(query.object_id)

            await self._auth.require_capability(
                query.requester_identity_id,
                obj,
                AclCapability.READ,
            )

            await self._audit.record(
                obj.object_id,
                query.requester_identity_id,
                query.requester_subject_type,
                query.requester_name,
                "READ",
            )

            return obj
