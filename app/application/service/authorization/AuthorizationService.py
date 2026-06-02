from app.application.port.outbound.permission.LoadPermissionPort import LoadPermissionPort
from app.common.constants.Capability import Capability
from app.common.exception.PermissionDeniedException import PermissionDeniedException
from app.domain.object.DataObject import DataObject

# Capabilities that PUBLIC objects expose without any ACL check
_PUBLIC_FREE_CAPS = frozenset({Capability.READ, Capability.DOWNLOAD})


class AuthorizationService:
    def __init__(self, load_permission_port: LoadPermissionPort) -> None:
        self._load_permission = load_permission_port

    async def require_capability(
        self,
        requester_identity_id: bytes,
        obj: DataObject,
        capability: Capability,
    ) -> None:
        # 1. PUBLIC object — READ / DOWNLOAD bypass ACL entirely
        if obj.is_public() and capability in _PUBLIC_FREE_CAPS:
            return

        # 2. Owner has full control over their own object
        if obj.owner_identity_id == requester_identity_id:
            return

        # 3. Load ACL entry for this (subject, object) pair
        permission = await self._load_permission.find_by_subject_and_object(
            subject_identity_id=requester_identity_id,
            object_id=obj.object_id,
        )
        if permission is None or not permission.has_capability(capability):
            raise PermissionDeniedException()
