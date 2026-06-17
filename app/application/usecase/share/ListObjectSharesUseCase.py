from app.application.dto.share.ListObjectSharesQuery import ListObjectSharesQuery
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.share.ObjectShareRepository import ObjectShareRepository
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.AppException import PublicError
from app.domain.object.model.ObjectShare import ObjectShare
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.capability.AclCapability import AclCapability


class ListObjectSharesUseCase:
    def __init__(
        self,
        load_object: LoadObjectPort,
        share_repository: ObjectShareRepository,
        authorization_service: AuthorizationService,
    ) -> None:
        self._load = load_object
        self._share = share_repository
        self._auth = authorization_service

    async def execute(self, query: ListObjectSharesQuery) -> list[ObjectShare]:
        obj = await self._load.find_by_id(query.object_id)
        if obj is None or obj.status == ObjectStatus.PURGED:
            raise PublicError("E067000")

        # Managing share links requires SHARE capability.
        await self._auth.require_capability(
            query.requester_identity_id, obj, AclCapability.SHARE
        )

        return await self._share.find_by_object(query.object_id)
