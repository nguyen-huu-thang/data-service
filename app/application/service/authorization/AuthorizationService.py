from app.application.port.outbound.permission.LoadPermissionPort import LoadPermissionPort
from app.application.port.outbound.permission.LoadSubjectPermissionPort import LoadSubjectPermissionPort
from app.domain.object.model.DataObject import DataObject
from app.domain.permission.capability.AclCapability import AclCapability
from app.domain.permission.capability.ObjectCapability import ObjectCapability
from app.common.exception.AppException import PublicError

# Capabilities that PUBLIC objects expose without any ACL check
_PUBLIC_FREE_CAPS = frozenset({AclCapability.READ, AclCapability.DOWNLOAD})

# ACL capability → system capability required to bypass per-object ACL
_SYSTEM_BYPASS: dict[AclCapability, ObjectCapability] = {
    AclCapability.READ: ObjectCapability.DATA_READ_ANY,
    AclCapability.WRITE: ObjectCapability.DATA_WRITE_ANY,
    AclCapability.DELETE: ObjectCapability.DATA_DELETE_ANY,
    AclCapability.SHARE: ObjectCapability.DATA_SHARE_ANY,
    AclCapability.DOWNLOAD: ObjectCapability.DATA_READ_ANY,
}


class AuthorizationService:
    def __init__(
        self,
        load_permission_port: LoadPermissionPort,
        load_subject_permission_port: LoadSubjectPermissionPort,
    ) -> None:
        self._load_permission = load_permission_port
        self._load_subject_permission = load_subject_permission_port

    async def require_capability(
        self,
        requester_identity_id: bytes,
        obj: DataObject,
        capability: AclCapability,
    ) -> None:
        # Checks are ordered cheapest-first: in-memory comparisons that cover
        # the common cases run before any database lookup, so the typical
        # "owner accesses their own object" path never touches the DB.

        # 1. Owner has full control over their own object
        if obj.owner_identity_id == requester_identity_id:
            return

        # 2. PUBLIC object — READ / DOWNLOAD bypass ACL entirely
        if obj.is_public() and capability in _PUBLIC_FREE_CAPS:
            return

        # 3. System Permission — DATA_X_ANY bypasses all per-object checks
        system_cap = _SYSTEM_BYPASS.get(capability)
        if system_cap is not None:
            subject_permissions = await self._load_subject_permission.find_by_subject(
                requester_identity_id
            )
            if any(sp.permission == system_cap for sp in subject_permissions):
                return

        # 4. Load ACL entry for this (subject, object) pair
        permission = await self._load_permission.find_by_subject_and_object(
            subject_identity_id=requester_identity_id,
            object_id=obj.object_id,
        )
        if permission is None or not permission.has_capability(capability):
            raise PublicError("E007004")
