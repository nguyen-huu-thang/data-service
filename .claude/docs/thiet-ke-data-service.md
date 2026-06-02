# Thiết kế Data Service

## Giới thiệu

Data Service là service lõi trong Base Platform, chịu trách nhiệm:

- Data storage infrastructure
- Object management
- Object permission
- Distributed data routing
- Blob storage abstraction
- Data ownership management
- Data lifecycle management

Data Service **không phải**: social post service, product service, document business service, media business service, application-specific storage.

Vai trò chính: **"Distributed data infrastructure của toàn platform"**

Phục vụ: user generated content, application data, binary data, documents, media, AI artifacts, system data.

---

## Triết lý thiết kế

| Tầng | Vai trò |
|---|---|
| Identity Service | Authentication infrastructure |
| Data Service | Data infrastructure |

Data Service **không quan tâm**: business meaning, application logic, nghiệp vụ cụ thể.

Data Service **chỉ quan tâm**: ownership, storage, permission, routing, lifecycle.

---

## Data Object Model

Mọi dữ liệu trong hệ thống đều là `DataObject`:

- image, file, video, document, dataset, AI artifact, attachment → đều là **DataObject**

Data Service không biết "đây là ảnh đại diện" hay "đây là ảnh sản phẩm" — đó là trách nhiệm của application service.

### Các trường của DataObject

```
object_id
owner_identity_id
tenant_id
object_type          (IMAGE, VIDEO, DOCUMENT, ARCHIVE, DATASET)
visibility           (PRIVATE, INTERNAL, PUBLIC)
status               (ACTIVE, ARCHIVED, SOFT_DELETED, PURGED)
current_version_id
storage_provider     (MINIO, CEPH, S3, FILESYSTEM)
storage_pointer      (địa chỉ vật lý blob — không lưu binary)
metadata_json        (metadata mở rộng, không chứa business data)
permission_version   (cache invalidation)
created_at
updated_at
```

---

## Identity-Centric Ownership

Mọi dữ liệu đều có owner. Owner luôn là `identity_id`.

Data Service không phụ thuộc `user-service` hay `profile-service` — chỉ biết `identity_id`.

Lợi ích: reusable architecture, domain independence, multi-subject support.

---

## Immutable Data Placement

```
owner identity_id → hash → partition → data shard (cố định mãi mãi)
```

Ví dụ:
```
identity A → DATA_SHARD_07
```

Mọi object mới của A đều vào `DATA_SHARD_07`. Không bao giờ đổi shard sau khi tạo.

---

## Sharding (Shared-Nothing)

Mỗi shard:
- Có database PostgreSQL riêng
- Có blob storage riêng
- Có metadata riêng
- Không có dữ liệu trùng lặp giữa các shard

Identity-aware sharding:
```
identity → hash → partition → data shard
```

Lợi ích: deterministic routing, không cần lookup toàn cluster, scale tuyến tính.

---

## Storage Model

Data Service tách riêng **Metadata** và **Blob**:

### Metadata (PostgreSQL)
- object id, owner, permission, tags, visibility, type

### Blob (MinIO / S3 / Filesystem / Ceph)
- Binary content thực tế

Metadata chứa `storage_pointer` — không chứa binary.

Ví dụ storage pointer:
```
storage://blob/abc123
bucket/path/file
```

---

## Authorization Model — Capability-Based

### Capability
```
READ, WRITE, DELETE, SHARE, DOWNLOAD, COMMENT
```

### Role (tập capability)
```
OWNER, EDITOR, CONTRIBUTOR, VIEWER
```

### ACL (object_permission)
Mỗi object có Access Control List:
```
identity A → OWNER
identity B → EDITOR
identity C → VIEWER
```

### Flow xác thực
```
request → JWT → identity_id → load ACL → evaluate capability → ALLOW / DENY
```

---

## Visibility Model

| Visibility | Ý nghĩa |
|---|---|
| PRIVATE | Chỉ owner |
| INTERNAL | Theo policy |
| PUBLIC | Không cần authorization |

---

## Data Routing

Mỗi object chứa `object_id` và `shard_id` → route trực tiếp, không cần global lookup.

**Data Search Service** chỉ dùng để resolve object location, không phải source of truth.

---

## Object Versioning

Mỗi object giữ:
- `current_version` — version hiện tại
- `historical_versions` — lịch sử version

Mỗi version có `content_hash` (SHA256) để integrity check và deduplicate trong tương lai.

---

## Event Model

Data Service phát sinh các event:

```
ObjectCreated
ObjectUpdated
ObjectDeleted
PermissionGranted
PermissionRevoked
ObjectShared
ObjectMoved
```

---

## Audit Model

Audit là bắt buộc — ghi nhận ai đọc, tải, sửa, xóa dữ liệu.

Audit có thể được lưu trong `audit-service` riêng.

---

## Data Lifecycle

```
ACTIVE → ARCHIVED → SOFT_DELETED → PURGED
```

- **ACTIVE**: bình thường
- **ARCHIVED**: lưu trữ, ít truy cập
- **SOFT_DELETED**: có thể restore
- **PURGED**: xóa vĩnh viễn

---

## Multi-Tenant

Mỗi object thuộc `tenant_id` và `owner_identity_id`.

```
tenant A, identity X   →   context độc lập
tenant B, identity X   →   context độc lập
```

---

## Object Reference Model

Business service không lưu blob — chỉ lưu `object_id`:

```
post-service:
  post └─ image_object_id

product-service:
  product └─ image_object_id
```

Data Service sở hữu dữ liệu thực.

---

## Tính năng dự kiến mở rộng (tương lai)

- Object versioning (đã có design)
- Object sharing (signed URL)
- Distributed cache
- CDN integration
- Chunk upload / resumable upload
- Object encryption
- Object replication
- Cold / archival storage

---

## Kiến trúc phân tán — Tổng kết

| Nguyên tắc | Mô tả |
|---|---|
| Distributed-first | Thiết kế cho phân tán từ đầu |
| Identity-centric ownership | Owner luôn là identity_id |
| Immutable placement | Shard không thay đổi sau khi tạo |
| Shard-aware routing | Routing trực tiếp từ shard_id |
| Capability-based authorization | Phân quyền theo capability |
| Shared-nothing architecture | Mỗi shard độc lập hoàn toàn |
| Horizontally scalable | Scale bằng thêm shard |
| Tenant-aware | Hỗ trợ multi-tenant |
