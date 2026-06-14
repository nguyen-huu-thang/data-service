from app.application.dto.version.ListVersionsQuery import ListVersionsQuery
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.version.LoadVersionPort import LoadVersionPort
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.AppException import PublicError
from app.domain.object.model.ObjectVersion import ObjectVersion
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.capability.AclCapability import AclCapability


class ListVersionsUseCase:
    def __init__(
        self,
        load_object: LoadObjectPort,
        load_version: LoadVersionPort,
        authorization_service: AuthorizationService,
    ) -> None:
        self._load = load_object
        self._load_version = load_version
        self._auth = authorization_service

    async def execute(self, query: ListVersionsQuery) -> list[ObjectVersion]:
        obj = await self._load.find_by_id(query.object_id)

        if obj is None or obj.status == ObjectStatus.PURGED:
            raise PublicError("E067000")

        await self._auth.require_capability(
            query.requester_identity_id, obj, AclCapability.READ
        )

        # find_by_object returns sorted ascending by version_number (see repository)
        return await self._load_version.find_by_object(query.object_id)
