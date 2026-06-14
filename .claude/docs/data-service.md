# Data Service

## Tổng quan

Data Service là dịch vụ lưu trữ dữ liệu trung tâm của Xime Platform.

Vai trò của Data Service là cung cấp hạ tầng lưu trữ dữ liệu dùng chung cho toàn bộ hệ sinh thái.

Data Service không chứa logic nghiệp vụ.

Data Service không biết:

* bài viết mạng xã hội
* sản phẩm thương mại điện tử
* tin nhắn
* hồ sơ người dùng

Data Service chỉ quản lý:

* Data Object
* Ownership
* Permission
* Lifecycle
* Versioning
* Storage
* Routing
* Audit

---

## Mục tiêu

Data Service được thiết kế để trở thành:

```text
Distributed Data Infrastructure
```

cho toàn bộ nền tảng.

Các mục tiêu chính:

* Generic
* Reusable
* Multi Application
* Multi Tenant
* Distributed First
* Horizontally Scalable

---

## Các nguyên tắc thiết kế

### DataObject First

Mọi dữ liệu đều được biểu diễn dưới dạng:

```text
DataObject
```

Ví dụ:

```text
Image
Video
Document
Dataset
AI Artifact
Attachment
Backup
```

đều được lưu dưới dạng DataObject.

Data Service không phân biệt ý nghĩa nghiệp vụ của dữ liệu.

---

### Metadata và Blob tách biệt

Data Service không lưu Binary trong Database.

Metadata được lưu trong PostgreSQL.

Binary được lưu trong Blob Storage.

Ví dụ:

```text
PostgreSQL
  └─ object metadata

Blob Storage
  └─ file content
```

---

### Subject Ownership

Mọi DataObject đều thuộc về một Subject.

Subject là thực thể có khả năng sở hữu dữ liệu.

Ví dụ:

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

---

### Application là Subject

Application được xem là một Subject hợp lệ.

Ví dụ:

```text
Xime Social
Xime Chat
Xime Shopping
```

Application có thể:

* sở hữu dữ liệu
* được cấp quyền hệ thống
* thực hiện thao tác trên Data Service

Application **không dùng JWT** (chốt 2026-06): service con của app được định danh bằng cert mang `owner_app_identity_id` (Trust khắc vào SAN); Data Service resolve subject APPLICATION trực tiếp từ cert. Chi tiết: [mo-hinh-subject-va-dinh-danh.md](mo-hinh-subject-va-dinh-danh.md).

---

### Service không phải Subject

Ví dụ:

```text
post-service
feed-service
search-service
identity-service
```

được xem là Runtime Service.

Service được xác thực bằng:

```text
service_id
certificate
shard_id
```

Service không sở hữu dữ liệu.

Service chỉ thực hiện hành động thay mặt Subject.

---

## Ownership Model

Mỗi DataObject có:

```text
owner_identity_id
owner_subject_type
```

Ví dụ:

```text
owner_identity_id = USER123
owner_subject_type = HUMAN
```

hoặc:

```text
owner_identity_id = APP001
owner_subject_type = APPLICATION
```

Owner là chủ sở hữu dữ liệu.

Owner không phải thực thể có quyền cao nhất.

---

## Authorization Model

Data Service sử dụng nhiều lớp quyền.

### System Permission

Quyền hệ thống.

Ví dụ:

```text
DATA_READ_ANY
DATA_WRITE_ANY
DATA_DELETE_ANY
DATA_RESTORE_ANY
DATA_SHARE_ANY
```

System Permission được cấp cho Subject.

---

### Object Permission

Quyền trên từng đối tượng dữ liệu.

Ví dụ:

```text
OWNER
EDITOR
VIEWER
```

---

### Ownership

Owner mặc định có toàn quyền trên dữ liệu của chính mình.

---

### Visibility

```text
PRIVATE
INTERNAL
PUBLIC
```

---

## Authorization Flow

```text
Request

↓

Subject Resolution

↓

System Permission Check

↓

Object Permission Check

↓

Ownership Check

↓

Visibility Check

↓

ALLOW / DENY
```

---

## Identity-Centric Placement

Data Service phân phối dữ liệu theo Identity.

```text
identity_id

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

Mọi dữ liệu của cùng một Identity sẽ được đặt trên cùng một Data Shard.

Placement là bất biến.

Không thay đổi sau khi tạo.

---

## Distributed Architecture

Data Service được thiết kế theo mô hình Shared-Nothing.

Mỗi Shard có:

```text
PostgreSQL riêng
Blob Storage riêng
Metadata riêng
```

Các Shard không chia sẻ dữ liệu trực tiếp.

Việc mở rộng hệ thống được thực hiện bằng cách thêm Shard mới.

---

## Versioning

Data Service hỗ trợ Versioning.

Một Object có thể có nhiều Version.

Ví dụ:

```text
Object

├─ Version 1
├─ Version 2
└─ Version 3
```

Version là bất biến.

Không chỉnh sửa.

Chỉ tạo mới.

---

## Lifecycle

Mỗi Object có vòng đời:

```text
ACTIVE

↓

ARCHIVED

↓

SOFT_DELETED

↓

PURGED
```

---

## Audit

Mọi thao tác trên dữ liệu đều phải có khả năng truy vết.

Ví dụ:

```text
READ
DOWNLOAD
UPDATE
DELETE
RESTORE
SHARE
```

Audit được sử dụng cho:

* Security
* Compliance
* Monitoring
* Incident Investigation

---

## Object Reference

Business Service không lưu Binary.

Business Service chỉ lưu:

```text
object_id
```

Ví dụ:

```text
Post

image_object_id
```

hoặc:

```text
Product

image_object_id
```

Data Service là nơi quản lý vòng đời thực sự của dữ liệu.

---

## Tenant Model

Tenant là ranh giới cô lập dữ liệu.

Ví dụ:

```text
tenant = null
```

Hệ sinh thái mặc định của Xime.

Hoặc:

```text
tenant = COMPANY_B
```

Khách hàng thuê nền tảng.

Tenant không phải Subject.

Tenant không sở hữu dữ liệu.

Tenant chỉ dùng để cô lập môi trường.

---

## Tích hợp với các dịch vụ khác

### Trust Service

Cung cấp:

```text
certificate
mTLS
service authentication
```

---

### Identity Service

Cung cấp:

```text
JWT
identity resolution
authentication
```

---

### User Service

Quản lý:

```text
HUMAN
```

---

### Application Service

Quản lý:

```text
APPLICATION
```

Nguồn sync trạng thái + System Permission cho subject APPLICATION (subject_cache, subject_permission).

---

### Agent Service

Quản lý:

```text
BOT
AI_AGENT
```

(Tên chốt thay cho "bot-service" trong tài liệu cũ - bao trùm bot, AI agent, robot phần cứng. Agent có credential và JWT qua Identity như HUMAN.)

---

## Tổng kết

Data Service là hạ tầng dữ liệu dùng chung cho toàn nền tảng.

Data Service không xử lý nghiệp vụ.

Data Service chỉ quản lý:

* Data Object
* Subject Ownership
* Permission
* Lifecycle
* Versioning
* Routing
* Audit
* Storage

Mục tiêu cuối cùng:

```text
Một nền tảng lưu trữ dữ liệu phân tán,
dùng chung cho toàn bộ hệ sinh thái Xime.
```
