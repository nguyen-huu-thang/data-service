from enum import StrEnum


class ObjectCapability(StrEnum):
    DATA_READ_ANY = "DATA_READ_ANY"

    DATA_WRITE_ANY = "DATA_WRITE_ANY"

    DATA_DELETE_ANY = "DATA_DELETE_ANY"

    DATA_SHARE_ANY = "DATA_SHARE_ANY"

    DATA_RESTORE_ANY = "DATA_RESTORE_ANY"

    DATA_AUDIT_READ = "DATA_AUDIT_READ"

    # Admin capability required to grant/revoke subject-level (system) permissions.
    # The very first holder must be seeded manually (no caller can self-grant it).
    # Quyền admin để cấp/thu hồi subject-permission (quyền hệ thống). Người giữ
    # đầu tiên phải seed thủ công (không caller nào tự cấp cho mình được).
    DATA_ADMIN_GRANT = "DATA_ADMIN_GRANT"