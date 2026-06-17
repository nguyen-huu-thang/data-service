from app.application.port.outbound.permission.LoadPermissionPort import LoadPermissionPort
from app.application.port.outbound.permission.LoadSubjectPermissionPort import LoadSubjectPermissionPort
from app.domain.object.model.DataObject import DataObject
from app.domain.permission.capability.AclCapability import AclCapability
from app.domain.permission.policy.AccessPolicy import AccessPolicy
from app.domain.sharedkernel.model.Id import Id
from app.common.exception.AppException import PublicError


class AuthorizationService:
    """
    Orchestrates authorization: loads ACL data via ports, delegates every
    decision to the pure domain AccessPolicy.

    Điều phối phân quyền: nạp dữ liệu ACL qua port, ủy quyền mọi quyết định cho
    AccessPolicy (domain thuần).
    """

    def __init__(
        self,
        load_permission_port: LoadPermissionPort,
        load_subject_permission_port: LoadSubjectPermissionPort,
        access_policy: AccessPolicy,
    ) -> None:
        self._load_permission = load_permission_port
        self._load_subject_permission = load_subject_permission_port
        self._policy = access_policy

    async def require_capability(
        self,
        requester_identity_id: Id,
        obj: DataObject,
        capability: AclCapability,
    ) -> None:
        # Checks are ordered cheapest-first: pure in-memory rules that cover the
        # common cases run before any database lookup, so the typical "owner
        # accesses their own object" path never touches the DB.

        # 1. Owner has full control over their own object
        if self._policy.is_owner(obj, requester_identity_id):
            return

        # 2. PUBLIC object — READ / DOWNLOAD bypass ACL entirely
        if self._policy.public_allows(obj, capability):
            return

        # 3. System Permission — DATA_X_ANY bypasses all per-object checks
        system_cap = self._policy.required_system_capability(capability)
        if system_cap is not None:
            subject_permissions = await self._load_subject_permission.find_by_subject(
                requester_identity_id
            )
            if self._policy.has_system_capability(subject_permissions, system_cap):
                return

        # 4. Load ACL entry for this (subject, object) pair
        permission = await self._load_permission.find_by_subject_and_object(
            subject_identity_id=requester_identity_id,
            object_id=obj.object_id,
        )
        if not self._policy.acl_allows(permission, capability):
            raise PublicError("E007004")
