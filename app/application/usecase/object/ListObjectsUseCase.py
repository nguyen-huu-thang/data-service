from app.application.dto.object.ListObjectsQuery import ListObjectsQuery
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.PermissionDeniedException import PermissionDeniedException
from app.domain.object.model.DataObject import DataObject
from app.domain.permission.capability.AclCapability import AclCapability


class ListObjectsUseCase:
    """
    List objects owned by a specific identity.

    Business flow:

    1. Verify requester can list the target owner's objects
    2. Load owner's objects
    3. Apply optional filters
    4. Return matching objects

    This use case is intended for owner-centric listings rather than
    discovery of all accessible objects in the system.
    """

    def __init__(
        self,
        load_object: LoadObjectPort,
        authorization_service: AuthorizationService,
    ) -> None:
        self._load = load_object
        self._auth = authorization_service

    async def execute(self, query: ListObjectsQuery) -> list[DataObject]:

        # Listing an owner's entire collection is considered a stronger
        # operation than reading a single object.
        #
        # Current rule:
        # - users may list their own objects
        # - listing another user's objects is denied
        #
        # Future versions may allow administrators with
        # DATA_READ_ANY privileges to bypass this restriction.
        if query.requester_identity_id != query.owner_identity_id:
            raise PermissionDeniedException()

        # Load objects belonging to the requested owner within the
        # specified tenant boundary.
        objects = await self._load.find_by_owner(
            query.owner_identity_id,
            tenant_id=query.tenant_id,
        )

        # Apply application-level filtering.
        #
        # Filters are optional and act on the already loaded result set.
        # If the dataset becomes large, these filters should move into
        # the repository implementation for efficiency.
        if query.object_type is not None:
            objects = [
                o
                for o in objects
                if o.object_type == query.object_type
            ]

        if query.status is not None:
            objects = [
                o
                for o in objects
                if o.status == query.status
            ]

        return objects