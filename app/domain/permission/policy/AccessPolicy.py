from app.domain.object.model.DataObject import DataObject
from app.domain.permission.capability.AclCapability import AclCapability
from app.domain.permission.capability.ObjectCapability import ObjectCapability
from app.domain.permission.model.ObjectPermission import ObjectPermission
from app.domain.permission.model.SubjectPermission import SubjectPermission
from app.domain.sharedkernel.model.Id import Id

# Capabilities that PUBLIC objects expose without any ACL check
# Quyền mà object PUBLIC cho phép không cần kiểm tra ACL
_PUBLIC_FREE_CAPS = frozenset({AclCapability.READ, AclCapability.DOWNLOAD})

# ACL capability → system capability required to bypass per-object ACL
# Quyền ACL → quyền hệ thống cần có để bỏ qua ACL từng-object
_SYSTEM_BYPASS: dict[AclCapability, ObjectCapability] = {
    AclCapability.READ: ObjectCapability.DATA_READ_ANY,
    AclCapability.WRITE: ObjectCapability.DATA_WRITE_ANY,
    AclCapability.DELETE: ObjectCapability.DATA_DELETE_ANY,
    AclCapability.SHARE: ObjectCapability.DATA_SHARE_ANY,
    AclCapability.DOWNLOAD: ObjectCapability.DATA_READ_ANY,
}


class AccessPolicy:
    """
    Pure access-control rules for objects (no I/O, no framework).

    The application layer loads data via ports and asks this policy to decide.
    Methods are intentionally fine-grained so the caller can short-circuit and
    avoid loading data it does not need (e.g. owner access never touches the DB).

    Quy tắc kiểm soát truy cập thuần (không I/O, không framework). Tầng application
    nạp dữ liệu qua port rồi hỏi policy. Các method tách nhỏ để caller dừng sớm,
    tránh nạp dữ liệu thừa (vd: chủ sở hữu không cần chạm DB).
    """

    def is_owner(self, obj: DataObject, requester_identity_id: Id) -> bool:
        return obj.owner_identity_id == requester_identity_id

    def public_allows(self, obj: DataObject, capability: AclCapability) -> bool:
        return obj.is_public() and capability in _PUBLIC_FREE_CAPS

    def required_system_capability(self, capability: AclCapability) -> ObjectCapability | None:
        return _SYSTEM_BYPASS.get(capability)

    def has_system_capability(
        self,
        subject_permissions: list[SubjectPermission],
        system_capability: ObjectCapability,
    ) -> bool:
        return any(sp.permission == system_capability for sp in subject_permissions)

    def acl_allows(
        self,
        object_permission: ObjectPermission | None,
        capability: AclCapability,
    ) -> bool:
        return object_permission is not None and object_permission.has_capability(capability)
