from app.application.dto.reference.ListObjectReferencesQuery import ListObjectReferencesQuery
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.reference.ObjectReferenceRepository import ObjectReferenceRepository
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.AppException import PublicError
from app.domain.object.model.ObjectReference import ObjectReference
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.capability.AclCapability import AclCapability


class ListObjectReferencesUseCase:
    def __init__(
        self,
        load_object: LoadObjectPort,
        reference_repository: ObjectReferenceRepository,
        authorization_service: AuthorizationService,
    ) -> None:
        self._load = load_object
        self._refs = reference_repository
        self._auth = authorization_service

    async def execute(self, query: ListObjectReferencesQuery) -> list[ObjectReference]:
        obj = await self._load.find_by_id(query.object_id)
        if obj is None or obj.status == ObjectStatus.PURGED:
            raise PublicError("E067000")

        await self._auth.require_capability(
            query.requester_identity_id, obj, AclCapability.READ
        )

        return await self._refs.find_by_object(query.object_id)
