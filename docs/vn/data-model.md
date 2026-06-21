# Data Model

[English](../en/data-model.md) | **Tiếng Việt**

---

## Nguyên tắc cốt lõi

Mọi thứ trong hệ thống đều là `DataObject`. Không có bảng chuyên biệt cho `image`, `video` hay `document`. Data Service chủ động không biết ý nghĩa nghiệp vụ — nó lưu object và theo dõi metadata.

```
image         ─┐
video          ├─→  DataObject  (type = IMAGE / VIDEO / DOCUMENT / ...)
document       ├─→
AI artifact    ├─→
dataset        ─┘
```

Application service chịu trách nhiệm gắn business context. Chúng chỉ lưu `object_id` làm tham chiếu.

---

## DataObject

Thực thể trung tâm của toàn bộ hệ thống.

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | binary(24) | Định danh object — 24-byte KSUID |
| `tenant_id` | varchar | Tenant context (`null` = platform mặc định) |
| `owner_identity_id` | binary(24) | **Identity sở hữu — mọi routing bắt đầu từ đây** |
| `shard_id` | varchar | Shard chứa object (VD: `DATA01`, `VN01`) |
| `object_type` | varchar | `IMAGE`, `VIDEO`, `DOCUMENT`, `ARCHIVE`, `DATASET` |
| `visibility` | varchar | `PRIVATE`, `INTERNAL`, `PUBLIC` |
| `status` | varchar | `ACTIVE`, `ARCHIVED`, `SOFT_DELETED`, `PURGED` |
| `current_version_id` | binary(24) | Tham chiếu tới version hiện tại |
| `storage_provider` | varchar | `LOCAL_DISK` |
| `storage_pointer` | varchar | Đường dẫn tương đối tới blob (VD: `ab12cd34/avatar.jpg`) |
| `metadata_json` | json | Metadata mở rộng (VD: `{"width": 1920, "height": 1080}`) |
| `permission_version` | int | Phiên bản ACL — dùng cho cache invalidation |
| `created_at` | timestamp | |
| `updated_at` | timestamp | |

### Domain Model

```python
@dataclass(frozen=True)
class DataObject:
    object_id: bytes           # 24-byte KSUID
    owner_identity_id: bytes   # identity sở hữu
    tenant_id: str | None
    shard_id: str
    object_type: ObjectType
    visibility: Visibility
    status: ObjectStatus
    current_version_id: bytes | None
    storage_pointer: str
    permission_version: int
    created_at: datetime
    updated_at: datetime

    def archive(self) -> 'DataObject':
        return replace(self, status=ObjectStatus.ARCHIVED, updated_at=_now())

    def soft_delete(self) -> 'DataObject':
        return replace(self, status=ObjectStatus.SOFT_DELETED, updated_at=_now())
```

---

## ObjectVersion

Mỗi lần nội dung của object thay đổi, một version mới được tạo ra. Version là bản ghi bất biến của nội dung trong quá khứ.

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | binary(24) | Định danh version |
| `object_id` | binary(24) | Object cha |
| `version_number` | int | Tuần tự: 1, 2, 3, ... |
| `storage_pointer` | varchar | Đường dẫn blob của version này |
| `content_hash` | varchar | SHA-256 — kiểm tra tính toàn vẹn và deduplicate sau này |
| `content_size` | bigint | Kích thước file (bytes) |
| `mime_type` | varchar | VD: `image/jpeg`, `application/pdf` |
| `created_by` | binary(24) | Identity tạo version |
| `created_at` | timestamp | |

---

## ObjectPermission

Access Control List của một object. Mỗi dòng gán một role cho một identity.

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | binary(24) | |
| `object_id` | binary(24) | |
| `subject_identity_id` | binary(24) | Identity được cấp quyền |
| `role` | varchar | `OWNER`, `EDITOR`, `CONTRIBUTOR`, `VIEWER` |
| `created_at` | timestamp | |

Ví dụ ACL cho `photo-001`:

```
identity A  →  OWNER
identity B  →  EDITOR
identity C  →  VIEWER
```

---

## ObjectCapability

Capability chi tiết theo từng object. Dùng khi mapping role mặc định chưa đủ.

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | binary(24) | |
| `permission_id` | binary(24) | Liên kết `object_permission` |
| `capability` | varchar | `READ`, `WRITE`, `DELETE`, `DOWNLOAD`, `SHARE`, `COMMENT` |

---

## ObjectReference

Theo dõi service nào đang sử dụng object. Giúp xóa an toàn — object chỉ được purge khi không còn service nào tham chiếu.

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | binary(24) | |
| `object_id` | binary(24) | |
| `service_id` | varchar | VD: `post-service`, `product-service` |
| `resource_type` | varchar | VD: `POST`, `PRODUCT`, `MESSAGE` |
| `resource_id` | varchar | ID thực thể nghiệp vụ |
| `created_at` | timestamp | |

---

## ObjectAudit

Audit trail cho mọi thao tác đọc, ghi, chia sẻ, xóa. Có thể lưu local hoặc chuyển sang audit service riêng.

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | binary(24) | |
| `object_id` | binary(24) | |
| `actor_identity_id` | binary(24) | Ai thực hiện thao tác |
| `action` | varchar | `READ`, `DOWNLOAD`, `UPDATE`, `DELETE`, `SHARE` |
| `created_at` | timestamp | |

---

## Tổng quan Schema Database

### MVP — 4 Bảng Cốt Lõi

4 bảng này đã đủ để xây avatar storage, attachment, document management, media storage, AI artifact storage và permission engine.

```
data_object
object_version
object_permission
object_reference
```

### Bảng Mở Rộng

```
object_capability   ← capability chi tiết (thêm khi cần)
object_tag          ← hỗ trợ tìm kiếm
object_share        ← chia sẻ công khai (tương lai: signed URL)
object_audit        ← audit trail
```

---

## Sharding Model

```
object mới → placement (dung lượng & tải) → shard_id → lưu cùng bản ghi
đọc/route → shard_id lấy từ bản ghi / tham chiếu (địa chỉ đi kèm dữ liệu)
```

Mỗi shard chạy bộ bảng đầy đủ, độc lập riêng:

```
DATA_SHARD_01
├── data_object
├── object_version
├── object_permission
├── object_capability
├── object_reference
├── object_tag
└── object_audit

DATA_SHARD_02
└── (schema tương tự, dữ liệu độc lập)
```

**Quy tắc quan trọng:**
- Shard của object do placement cấp lúc tạo (theo dung lượng & tải) và lưu cố định vào `shard_id`, không bao giờ thay đổi
- Route bằng `shard_id` lưu sẵn / mang theo trong tham chiếu — KHÔNG tính lại từ `identity_id`
- Không cross-shard query trong một request đơn

---

## Index Quan Trọng

```sql
-- data_object: hầu hết query lọc theo owner + tenant + status
CREATE INDEX idx_data_object_owner ON data_object (owner_identity_id, tenant_id, status, object_type);

-- object_permission: lookup ACL theo subject
CREATE INDEX idx_object_perm_subject ON object_permission (subject_identity_id, object_id);

-- object_version: liệt kê version của object
CREATE INDEX idx_object_version_parent ON object_version (object_id);

-- object_reference: kiểm tra reference trước khi xóa
CREATE INDEX idx_object_ref_object ON object_reference (object_id);
```

---

## Thiết kế ID — KSUID

Tất cả định danh đều là 24-byte KSUID (K-Sortable Unique Identifier):

```
4 bytes timestamp + 20 bytes random  =  24 bytes tổng cộng
```

Đặc tính:
- **Sortable**: object mới hơn có ID lớn hơn theo thứ tự từ điển
- **Unique**: 20 bytes random — xác suất trùng không đáng kể
- **Opaque**: không encode thông tin nhạy cảm
- **Compact**: 24 bytes so với 36 bytes của UUID string

```python
import os, struct, time

KSUID_EPOCH = 1_400_000_000  # ~ Tháng 5/2014

def generate_id() -> bytes:
    ts = int(time.time()) - KSUID_EPOCH
    return struct.pack('>I', ts) + os.urandom(20)
```
