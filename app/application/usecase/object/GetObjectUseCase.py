from core.transaction.manager import TransactionManager

from app.application.dto.object.GetObjectQuery import GetObjectQuery
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.service.audit.AuditService import AuditService
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.constants.Capability import Capability
from app.common.constants.ObjectStatus import ObjectStatus
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.domain.object.DataObject import DataObject


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
                Capability.READ,
            )

            await self._audit.record(obj.object_id, query.requester_identity_id, "READ")

            return obj
