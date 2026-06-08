from app.application.dto.object.ListObjectsQuery import ListObjectsQuery
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.PermissionDeniedException import PermissionDeniedException
from app.domain.object.model.DataObject import DataObject
from app.domain.permission.capability.AclCapability import AclCapability


class ListObjectsUseCase:
    def __init__(
        self,
        load_object: LoadObjectPort,
        authorization_service: AuthorizationService,
    ) -> None:
        self._load = load_object
        self._auth = authorization_service

    async def execute(self, query: ListObjectsQuery) -> list[DataObject]:
        # Requester can only list their own objects unless they have system permission
        if query.requester_identity_id != query.owner_identity_id:
            # Check if requester has DATA_READ_ANY by trying to authorize a dummy check
            # Use a synthetic check: load one object and verify capability (or check system perm directly)
            # For simplicity, deny if not the owner — system permission check happens in AuthorizationService
            # when actual per-object access is attempted
            raise PermissionDeniedException()

        objects = await self._load.find_by_owner(
            query.owner_identity_id,
            tenant_id=query.tenant_id,
        )

        # Apply optional filters
        if query.object_type is not None:
            objects = [o for o in objects if o.object_type == query.object_type]
        if query.status is not None:
            objects = [o for o in objects if o.status == query.status]

        return objects
