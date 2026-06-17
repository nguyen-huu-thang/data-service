from xime.core.transaction.manager import TransactionManager

from app.application.dto.object.GetObjectQuery import GetObjectQuery
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.service.audit.AuditService import AuditService
from app.domain.audit.valueobject.AuditAction import AuditAction
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.AppException import PublicError
from app.domain.object.model.DataObject import DataObject
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.capability.AclCapability import AclCapability


class GetObjectUseCase:
    """
    Retrieve object metadata.

    Business flow:

    1. Load object
    2. Ensure object exists and is not purged
    3. Verify requester can read the object
    4. Write audit record
    5. Return object metadata

    This use case only returns object metadata.
    Blob content retrieval is handled separately by DownloadObjectUseCase.
    """

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
        # Metadata lookup, authorization and audit logging are executed
        # within a single transaction scope.
        async with self._tx():

            # Load object metadata.
            obj = await self._load.find_by_id(query.object_id)

            # Purged objects are treated as non-existent.
            #
            # Clients should not be able to distinguish between
            # "never existed" and "permanently removed".
            if obj is None or obj.status == ObjectStatus.PURGED:
                raise PublicError("E067000")

            # Read permission is required.
            #
            # AuthorizationService grants access when:
            # - requester has DATA_READ_ANY system permission
            # - requester is object owner
            # - requester has READ capability in object ACL
            # - object is PUBLIC
            await self._auth.require_capability(
                query.requester_identity_id,
                obj,
                AclCapability.READ,
            )

            # Record metadata access for auditing and compliance.
            await self._audit.record(
                query.object_id,
                query.requester_identity_id,
                query.requester_subject_type,
                query.requester_name,
                AuditAction.READ,
            )

            return obj
