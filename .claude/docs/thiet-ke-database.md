# Thiết kế Database — Data Service

> Đây là thiết kế tham khảo cho Data Service.
>
> Mục tiêu:
>
> * Generic
> * Reusable
> * Distributed-first
> * Subject-centric
> * Permission-aware
> * Application-aware
> * Shard-friendly

---

## Nguyên tắc thiết kế

Data Service không hiểu business domain.

Data Service không tạo các bảng:

```text
image
video
avatar
product_image
chat_attachment
```

Mọi dữ liệu đều là:

```text
DataObject
```

Database chỉ lưu metadata.

Binary luôn nằm ở Blob Storage.

---

## Subject Model

Data Service sử dụng Subject làm đơn vị sở hữu dữ liệu.

Subject là:

```text
HUMAN
BOT
AI_AGENT
APPLICATION
```

Mỗi Subject có:

```text
identity_id
subject_type
name
```

Ví dụ:

```text
identity_id = 01ABC...
subject_type = HUMAN
name = Nguyen Van A
```

hoặc:

```text
identity_id = 01XYZ...
subject_type = APPLICATION
name = Xime Social
```

Data Service cache Subject Information để:

* Audit
* Logging
* Monitoring
* Authorization
* Incident Investigation

Source of truth nằm ở service quản lý Subject.

---

## System Permission Model

Data Service hỗ trợ hai loại quyền:

## System Permission

Quyền hệ thống.

Ví dụ:

```text
DATA_READ_ANY
DATA_WRITE_ANY
DATA_DELETE_ANY
DATA_RESTORE_ANY
DATA_SHARE_ANY
```

Quyền này thuộc về Subject.

Ví dụ:

```text
Xime Social

DATA_CREATE_OBJECT
DATA_READ_OBJECT
```

Hoặc:

```text
Moderation System

DATA_DELETE_ANY
```

---

## Object Permission

Quyền trên từng DataObject cụ thể.

Ví dụ:

```text
READ
WRITE
DELETE
SHARE
DOWNLOAD
```

---

## MVP Database Tables

## 1. data_object

Bảng trung tâm của toàn hệ thống.

| Trường             | Kiểu       | Mô tả                                  |
| ------------------ | ---------- | -------------------------------------- |
| id                 | binary(24) | Object ID                              |
| tenant_id          | varchar    | Tenant sở hữu môi trường               |
| shard_id           | varchar    | Data shard                             |
| owner_identity_id  | binary(24) | Chủ sở hữu                             |
| owner_subject_type | varchar    | HUMAN/BOT/AI_AGENT/APPLICATION         |
| object_type        | varchar    | IMAGE, VIDEO, DOCUMENT, DATASET        |
| visibility         | varchar    | PRIVATE, INTERNAL, PUBLIC              |
| status             | varchar    | ACTIVE, ARCHIVED, SOFT_DELETED, PURGED |
| current_version_id | binary(24) | Version hiện tại                       |
| storage_provider   | varchar    | LOCAL_DISK                             |
| storage_pointer    | varchar    | Địa chỉ blob                           |
| metadata_json      | json       | Metadata mở rộng                       |
| permission_version | int        | ACL version                            |
| created_at         | timestamp  |                                        |
| updated_at         | timestamp  |                                        |

---

## 2. object_version

Version bất biến của dữ liệu.

| Trường                  | Kiểu       |
| ----------------------- | ---------- |
| id                      | binary(24) |
| object_id               | binary(24) |
| version_number          | int        |
| storage_pointer         | varchar    |
| content_hash            | varchar    |
| content_size            | bigint     |
| mime_type               | varchar    |
| created_by_identity_id  | binary(24) |
| created_by_subject_type | varchar    |
| created_at              | timestamp  |

Nguyên tắc:

```text
Version không sửa.

Chỉ tạo mới.
```

---

## 3. object_permission

ACL của từng Object.

| Trường              | Kiểu       |
| ------------------- | ---------- |
| id                  | binary(24) |
| object_id           | binary(24) |
| subject_identity_id | binary(24) |
| subject_type        | varchar    |
| role                | varchar    |
| created_at          | timestamp  |

Ví dụ:

```text
USER_A → OWNER
USER_B → EDITOR
BOT_C → VIEWER
APPLICATION_X → EDITOR
```

---

## 4. subject_cache

Cache Subject Information.

Source of truth không nằm ở Data Service.

| Trường       | Kiểu       |
| ------------ | ---------- |
| identity_id  | binary(24) |
| subject_type | varchar    |
| name         | varchar    |
| updated_at   | timestamp  |

Mục đích:

```text
Audit
Logging
Debug
Monitoring
```

---

## 5. subject_permission

Cache quyền hệ thống.

Source of truth nằm ở Subject Service hoặc Application Service.

| Trường              | Kiểu       |
| ------------------- | ---------- |
| id                  | binary(24) |
| subject_identity_id | binary(24) |
| subject_type        | varchar    |
| permission          | varchar    |
| created_at          | timestamp  |
| updated_at          | timestamp  |

Ví dụ:

```text
APP_XIME_SOCIAL

DATA_CREATE_OBJECT
DATA_READ_OBJECT
```

Hoặc:

```text
MODERATION_SYSTEM

DATA_DELETE_ANY
```

---

## 6. object_reference

Theo dõi Application đang sử dụng Object.

| Trường                  | Kiểu       |
| ----------------------- | ---------- |
| id                      | binary(24) |
| object_id               | binary(24) |
| application_identity_id | binary(24) |
| application_name        | varchar    |
| resource_type           | varchar    |
| resource_id             | varchar    |
| created_at              | timestamp  |

Ví dụ:

```text
Object A

được sử dụng bởi

Xime Social

POST

POST_123
```

Data Service không quan tâm Service nào đang dùng.

Data Service chỉ quan tâm Application nào đang sở hữu quan hệ nghiệp vụ với Object.

---

## 7. object_tag

Hỗ trợ tìm kiếm.

| Trường    | Kiểu       |
| --------- | ---------- |
| object_id | binary(24) |
| tag       | varchar    |

Ví dụ:

```text
invoice
contract
customer-a
```

---

## 8. object_share

Public Sharing.

| Trường      | Kiểu       |
| ----------- | ---------- |
| id          | binary(24) |
| object_id   | binary(24) |
| share_token | varchar    |
| expires_at  | timestamp  |
| created_at  | timestamp  |

---

## 9. object_audit

Audit cục bộ nếu chưa có Audit Service.

| Trường             | Kiểu       |
| ------------------ | ---------- |
| id                 | binary(24) |
| object_id          | binary(24) |
| actor_identity_id  | binary(24) |
| actor_subject_type | varchar    |
| actor_name         | varchar    |
| action             | varchar    |
| created_at         | timestamp  |

Ví dụ:

```text
READ
DOWNLOAD
UPDATE
DELETE
RESTORE
SHARE
```

---

## Tương lai

## object_governance

Governance Layer.

Ví dụ:

```text
legal_hold
retention_policy
moderation_lock
```

---

## object_replica

Replication Layer.

Ví dụ:

```text
PRIMARY
SECONDARY
ARCHIVE
```

---

## Index quan trọng

## data_object

```text
(owner_identity_id)

(owner_identity_id, status)

(owner_identity_id, object_type)

(shard_id)

(status)
```

---

## object_permission

```text
(subject_identity_id)

(object_id)

(subject_identity_id, object_id)
```

---

## subject_permission

```text
(subject_identity_id)

(permission)
```

---

## object_reference

```text
(application_identity_id)

(object_id)
```

---

## Sharding Model

```text
owner_identity_id

↓

hash

↓

partition

↓

data shard
```

Ví dụ:

```text
USER_A

↓

DATA_SHARD_07
```

Placement là bất biến.

Không đổi shard sau khi tạo.

---

## Storage Architecture

```text
PostgreSQL

↓

data_object

↓

storage_pointer

↓

Blob Storage
```

Ví dụ:

```text
Local Disk
MinIO
S3
Ceph
```

Database không lưu binary.

Database chỉ lưu metadata.

---

## Kiến trúc Database — Tổng kết

| Nguyên tắc                  | Mô tả                           |
| --------------------------- | ------------------------------- |
| Subject Ownership           | Dữ liệu thuộc Subject           |
| Application Aware           | Application là Subject hợp lệ   |
| Runtime-Service Independent | Không phụ thuộc Service Runtime |
| System Permission           | Quyền hệ thống riêng            |
| Object Permission           | ACL riêng                       |
| Shared Nothing              | Mỗi Shard độc lập               |
| Immutable Versioning        | Version không sửa               |
| Auditability                | Mọi hành động đều truy vết      |
| Identity-Centric Placement  | Placement theo Identity         |
| Distributed First           | Thiết kế cho phân tán           |
