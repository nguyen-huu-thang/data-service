# Phân quyền

[English](../en/authorization.md) | **Tiếng Việt**

---

## Mô hình

Data Service sử dụng **Capability-Based Access Control (CBAC)**. Quyền truy cập vào một object được xác định bằng cách đánh giá capability của identity yêu cầu dựa trên ACL của object.

---

## Capability

Capability đại diện cho một hành động cụ thể có thể thực hiện trên object:

| Capability | Mô tả |
|---|---|
| `READ` | Xem metadata của object |
| `WRITE` | Tải lên version mới / cập nhật metadata |
| `DELETE` | Soft-delete object |
| `DOWNLOAD` | Lấy nội dung nhị phân (blob) |
| `SHARE` | Cấp hoặc thu hồi quyền cho identity khác |
| `COMMENT` | Thêm comment (tương lai) |

---

## Role

Role là tập capability được định nghĩa sẵn. Gán role cho một identity là cách chính để cấp quyền truy cập.

| Role | Capability |
|---|---|
| `OWNER` | READ, WRITE, DELETE, DOWNLOAD, SHARE |
| `EDITOR` | READ, WRITE, DOWNLOAD |
| `CONTRIBUTOR` | READ, WRITE |
| `VIEWER` | READ, DOWNLOAD |

Role owner được tự động gán cho `owner_identity_id` khi tạo object.

Có thể gán capability chi tiết hơn cho từng identity qua bảng `object_capability` khi mapping role mặc định chưa đủ.

---

## Cấu trúc ACL

Mỗi object có Access Control List được lưu trong `object_permission`:

```
object photo-001:
  identity-A  →  OWNER       (READ, WRITE, DELETE, DOWNLOAD, SHARE)
  identity-B  →  EDITOR      (READ, WRITE, DOWNLOAD)
  identity-C  →  VIEWER      (READ, DOWNLOAD)
```

---

## Visibility

Trường `visibility` trên `DataObject` cung cấp kiểm soát truy cập ở mức thô:

| Visibility | Hành vi truy cập |
|---|---|
| `PRIVATE` | Chỉ identity nằm trong ACL |
| `INTERNAL` | Theo policy (VD: mọi identity trong cùng tenant) |
| `PUBLIC` | Không cần authorization cho READ/DOWNLOAD |

Kiểm tra visibility xảy ra trước khi evaluate ACL. Object `PUBLIC` bỏ qua ACL cho read/download.

---

## Luồng Xác Thực

```
Request đến
      ↓
Lấy JWT từ header
      ↓
Xác minh chữ ký JWT    ← dùng public key từ Trust Service cache
      ↓
Lấy identity_id từ JWT claims
      ↓
Giải quyết shard của object    ← từ object_id hoặc owner_identity_id
      ↓
Kiểm tra visibility của object
      ↓ (nếu không phải PUBLIC)
Load ACL từ bảng object_permission
      ↓
Đánh giá: identity có capability cần thiết không?
      ↓
ALLOW  /  DENY
```

Tất cả các bước xảy ra trong Data Service — không gọi service authorization bên ngoài lúc xử lý request.

---

## Triển khai

Authorization logic nằm trong `application/service/authorization/`:

```python
class AuthorizationService:
    def __init__(
        self,
        load_permission_port: LoadPermissionPort,
    ) -> None:
        self._load_permission = load_permission_port

    async def check(
        self,
        identity_id: bytes,
        object_id: bytes,
        required: Capability,
    ) -> bool:
        permissions = await self._load_permission.find_by_object(object_id)
        for perm in permissions:
            if perm.subject_identity_id == identity_id:
                return required in perm.role.capabilities()
        return False
```

Use case gọi `AuthorizationService` trước khi thực hiện bất kỳ thao tác thay đổi trạng thái nào:

```python
class DeleteObjectUseCase:
    async def execute(self, command: DeleteObjectCommand) -> None:
        allowed = await self._auth.check(
            command.requester_identity_id,
            command.object_id,
            Capability.DELETE,
        )
        if not allowed:
            raise PermissionDeniedError(command.object_id)
        # ... tiến hành xóa
```

---

## Chia sẻ (Sharing)

Chia sẻ là hành động cấp hoặc thu hồi quyền truy cập vào object cho identity khác. Chỉ identity có capability `SHARE` (tức là role `OWNER`) mới thực hiện được.

```
identity-A (OWNER) gọi: grant_permission(object_id, identity-D, role=VIEWER)
      ↓
AuthorizationService.check(identity-A, object_id, SHARE)  → ALLOW
      ↓
GrantPermissionUseCase: insert vào object_permission
```

---

## Permission Versioning

Trường `permission_version` trên `DataObject` được tăng lên mỗi khi ACL thay đổi. Được dùng bởi downstream cache để invalidate dữ liệu permission cũ mà không cần flush toàn bộ cache.

---

## Data Service KHÔNG làm gì trong Authorization

- Không thực hiện platform-level authorization (admin, platform role) — đó là trách nhiệm của Identity Service
- Không gọi authorization service bên ngoài trên mỗi request — ACL được evaluate cục bộ
- Không implement attribute-based policy (ABAC) — chỉ dùng capability-based role
