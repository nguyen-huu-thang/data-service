from app.application.dto.tag.ListObjectTagsQuery import ListObjectTagsQuery
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.tag.ObjectTagRepository import ObjectTagRepository
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.AppException import PublicError
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.object.valueobject.ObjectTag import ObjectTag
from app.domain.permission.capability.AclCapability import AclCapability


class ListObjectTagsUseCase:
    def __init__(
        self,
        load_object: LoadObjectPort,
        tag_repository: ObjectTagRepository,
        authorization_service: AuthorizationService,
    ) -> None:
        self._load = load_object
        self._tags = tag_repository
        self._auth = authorization_service

    async def execute(self, query: ListObjectTagsQuery) -> list[ObjectTag]:
        obj = await self._load.find_by_id(query.object_id)
        if obj is None or obj.status == ObjectStatus.PURGED:
            raise PublicError("E067000")

        await self._auth.require_capability(
            query.requester_identity_id, obj, AclCapability.READ
        )

        return await self._tags.find_tags(query.object_id)
