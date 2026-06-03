# Thiết kế Database — Data Service

> Đây là thiết kế tham khảo, có thể chỉnh sửa nhiều trong tương lai.

## Nguyên tắc thiết kế

- Generic, reusable, shard-friendly, identity-centric, permission-aware
- **Không** tạo bảng `image`, `video`, `document`, `attachment` — điều này khiến Data Service hiểu business
- Mọi dữ liệu đều là `DataObject`
- Database chỉ lưu metadata, **không** lưu binary
- Mỗi shard có bộ bảng riêng (shared-nothing)

---

## MVP — 4 bảng cốt lõi

Giai đoạn đầu chỉ cần 4 bảng này đã đủ để build avatar storage, attachment, document, media, AI artifact, permission engine:

1. `data_object`
2. `object_version`
3. `object_permission`
4. `object_reference`

---

## Bảng: data_object

Bảng trung tâm của toàn bộ hệ thống.

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | binary(24) | Định danh object |
| `tenant_id` | varchar | Tenant sở hữu (null = platform mặc định) |
| `owner_identity_id` | binary(24) | **Identity sở hữu — mọi routing bắt đầu từ đây** |
| `shard_id` | varchar | Shard chứa object (VD: DATA01, VN01) |
| `object_type` | varchar | IMAGE, VIDEO, DOCUMENT, ARCHIVE, DATASET |
| `visibility` | varchar | PRIVATE, INTERNAL, PUBLIC |
| `status` | varchar | ACTIVE, ARCHIVED, SOFT_DELETED, PURGED |
| `current_version_id` | binary(24) | Version hiện tại |
| `storage_provider` | varchar | LOCAL_DISK |
| `storage_pointer` | varchar | Địa chỉ vật lý blob (VD: bucket-a/image/abc.jpg) |
| `metadata_json` | json | Metadata mở rộng (VD: `{"width": 1920, "height": 1080}`) |
| `permission_version` | int | Version ACL — dùng cho cache invalidation |
| `created_at` | timestamp | |
| `updated_at` | timestamp | |

---

## Bảng: object_version

Mỗi lần object thay đổi nội dung → sinh version mới.

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | binary(24) | Version id |
| `object_id` | binary(24) | Object cha |
| `version_number` | int | 1, 2, 3, ... |
| `storage_pointer` | varchar | Địa chỉ blob của version này |
| `content_hash` | varchar | SHA256 — dùng cho integrity check và deduplicate |
| `content_size` | bigint | Kích thước file (bytes) |
| `mime_type` | varchar | VD: image/jpeg, application/pdf |
| `created_by` | binary(24) | Identity tạo version |
| `created_at` | timestamp | |

---

## Bảng: object_permission

ACL của object — ai có quyền gì.

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | binary(24) | |
| `object_id` | binary(24) | |
| `subject_identity_id` | binary(24) | Identity được cấp quyền |
| `role` | varchar | OWNER, EDITOR, CONTRIBUTOR, VIEWER |
| `created_at` | timestamp | |

Ví dụ:
```
photo-001:
  userA → OWNER
  userB → EDITOR
  userC → VIEWER
```

---

## Bảng: object_capability

Capability chi tiết (bổ sung sau object_permission nếu cần granular control).

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | binary(24) | |
| `permission_id` | binary(24) | Liên kết object_permission |
| `capability` | varchar | READ, WRITE, DELETE, DOWNLOAD, SHARE, COMMENT |

---

## Bảng: object_reference

Theo dõi object đang được service nào sử dụng.

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | binary(24) | |
| `object_id` | binary(24) | |
| `service_id` | varchar | VD: post-service, product-service |
| `resource_type` | varchar | VD: POST, PRODUCT, MESSAGE |
| `resource_id` | varchar | ID thực thể business |
| `created_at` | timestamp | |

---

## Bảng: object_tag

Hỗ trợ tìm kiếm.

| Trường | Kiểu | Mô tả |
|---|---|---|
| `object_id` | binary(24) | |
| `tag` | varchar | VD: invoice, 2026, customer-a |

---

## Bảng: object_share (tương lai)

Hỗ trợ public sharing (tương tự Google Drive public link).

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | binary(24) | |
| `object_id` | binary(24) | |
| `share_token` | varchar | Token public |
| `expires_at` | timestamp | |
| `created_at` | timestamp | |

---

## Bảng: object_audit

Nếu chưa có audit-service riêng.

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | binary(24) | |
| `object_id` | binary(24) | |
| `actor_identity_id` | binary(24) | |
| `action` | varchar | READ, DOWNLOAD, UPDATE, DELETE, SHARE |
| `created_at` | timestamp | |

---

## Index quan trọng

```
data_object:
  (owner_identity_id, tenant_id, status, object_type)

object_permission:
  (subject_identity_id, object_id)

object_reference:
  (object_id)

object_version:
  (object_id)
```

---

## Sharding Model

```
identity_id → hash → partition → data shard
```

- Identity quyết định data placement
- Không đổi shard sau khi tạo
- Mỗi shard có bộ bảng riêng hoàn toàn độc lập

### Ví dụ cấu trúc mỗi shard

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
├── (tương tự)
```

---

## Tách Storage khỏi Database

```
PostgreSQL
  └── data_object
        └── storage_pointer (relative path)
              └── Local Disk (served via FastAPI)
                    └── binary file thực tế
```

Lợi ích:
- Database nhỏ, hiệu quả
- Scale blob storage độc lập với metadata
- Backup riêng biệt
- Dễ đổi storage backend
