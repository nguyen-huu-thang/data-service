from app.application.dto.version.GetVersionQuery import GetVersionQuery
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.version.LoadVersionPort import LoadVersionPort
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.domain.object.model.ObjectVersion import ObjectVersion
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.capability.AclCapability import AclCapability


class GetVersionUseCase:
    def __init__(
        self,
        load_object: LoadObjectPort,
        load_version: LoadVersionPort,
        authorization_service: AuthorizationService,
    ) -> None:
        self._load = load_object
        self._load_version = load_version
        self._auth = authorization_service

    async def execute(self, query: GetVersionQuery) -> ObjectVersion:
        obj = await self._load.find_by_id(query.object_id)

        if obj is None or obj.status == ObjectStatus.PURGED:
            raise ObjectNotFoundException(query.object_id)

        await self._auth.require_capability(
            query.requester_identity_id, obj, AclCapability.READ
        )

        version = await self._load_version.find_by_id(query.version_id)

        # Not found OR belongs to a different object — return not found to avoid info leak
        if version is None or version.object_id != query.object_id:
            raise ObjectNotFoundException(query.version_id)

        return version
