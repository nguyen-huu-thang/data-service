# Thiết kế Data Service

## Giới thiệu

Data Service là một service lõi trong Base Platform, chịu trách nhiệm:

* Data storage infrastructure
* Object management
* Object permission
* Distributed data routing
* Blob storage abstraction
* Data ownership management
* Data lifecycle management

Data Service không phải:

* Social Post Service
* Product Service
* Document Business Service
* Media Business Service
* Application-specific Storage Service

Vai trò chính:

Distributed Data Infrastructure của toàn Platform.

Data Service phục vụ:

* User Generated Content
* Application Data
* Binary Data
* Documents
* Media
* AI Artifacts
* System Data

---

## Triết lý thiết kế

| Thành phần       | Vai trò                       |
| ---------------- | ----------------------------- |
| Trust Service    | Runtime Trust Infrastructure  |
| Identity Service | Authentication Infrastructure |
| Data Service     | Data Infrastructure           |

Data Service không quan tâm:

* Business Meaning
* Application Logic
* Domain-specific Rules

Data Service chỉ quan tâm:

* Ownership
* Permission
* Routing
* Storage
* Lifecycle
* Audit

---

## Data Object Model

Mọi dữ liệu trong hệ thống đều là DataObject.

Ví dụ:

* Image
* Video
* Document
* Dataset
* AI Artifact
* Attachment
* Backup Object

đều được biểu diễn bằng:

```text
DataObject
```

Data Service không biết:

```text
đây là ảnh đại diện
đây là ảnh sản phẩm
đây là ảnh bài viết
```

Đó là trách nhiệm của Application Service.

---

## Subject Model

Mọi dữ liệu đều thuộc về một Subject.

Subject là bất kỳ thực thể nào có khả năng sở hữu dữ liệu.

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

Ví dụ:

```text
identity_id = 01ABC...
subject_type = HUMAN
name = Nguyen Van A
```

Hoặc:

```text
identity_id = 01XYZ...
subject_type = APPLICATION
name = Xime Social
```

Identity ID là định danh duy nhất toàn hệ thống.

Subject Type dùng để:

* Validation
* Authorization
* Audit
* Debugging

Name dùng để:

* Logging
* Monitoring
* Điều tra sự cố
* Hỗ trợ vận hành

---

## Application Subject

Application là một Subject.

Ví dụ:

```text
Xime Social
Xime Chat
Xime Shopping
```

Application có:

```text
identity_id
subject_type = APPLICATION
name
permissions
```

Application có thể:

* Sở hữu dữ liệu
* Được cấp quyền hệ thống
* Thực hiện hành động trên Data Service

Application khác với Service.

Ví dụ:

```text
Xime Social
```

là Application.

Trong khi:

```text
post-service
feed-service
search-service
```

chỉ là runtime component.

---

## Runtime Service Identity

Data Service phân biệt rõ:

## Subject

Thực thể kinh doanh.

Ví dụ:

```text
HUMAN
BOT
AI_AGENT
APPLICATION
```

Có:

```text
identity_id
```

---

## Service

Thực thể runtime.

Ví dụ:

```text
post-service
feed-service
search-service
identity-service
```

Có:

```text
service_id
certificate
shard_id
```

Được Trust Service quản lý.

Service không sở hữu dữ liệu.

Service chỉ đại diện cho một tiến trình đang chạy.

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

Hoặc:

```text
owner_identity_id = APP001
owner_subject_type = APPLICATION
```

Owner là chủ sở hữu dữ liệu.

Owner không nhất thiết là thực thể có quyền cao nhất.

---

## Authorization Model

Data Service sử dụng nhiều lớp quyền.

## 1. System Permission

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

Ví dụ:

```text
Xime Social
Xime Chat
Xime Shopping
```

hoặc các Subject hệ thống khác.

Nếu Subject có:

```text
DATA_DELETE_ANY
```

thì có thể xóa dữ liệu mà không cần là Owner.

---

## 2. Object Permission

Quyền trên từng đối tượng cụ thể.

Ví dụ:

```text
READ
WRITE
DELETE
SHARE
DOWNLOAD
```

---

## 3. Ownership Rule

Owner mặc định có toàn bộ quyền đối với dữ liệu của chính mình.

---

## 4. Visibility Rule

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

## Identity-Centric Routing

Data placement vẫn dựa trên Identity.

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
identity A

↓

DATA_SHARD_07
```

Mọi dữ liệu của Identity A sẽ nằm trên cùng một Data Shard.

Placement là bất biến.

Không thay đổi sau khi tạo.

---

## Shared-Nothing Sharding

Mỗi Shard có:

* PostgreSQL riêng
* Blob Storage riêng
* Metadata riêng

Không chia sẻ dữ liệu trực tiếp với Shard khác.

---

## Storage Model

Metadata và Blob được tách biệt.

## Metadata

PostgreSQL:

```text
object
permission
version
audit
```

## Blob

Local Disk hoặc Storage Adapter:

```text
filesystem
object storage
cloud storage
```

Data Service chỉ lưu:

```text
storage_pointer
```

không lưu binary trong database.

---

## Object Versioning

Object gồm:

```text
current_version
historical_versions
```

Mỗi version:

```text
content_hash
content_size
mime_type
created_by
created_at
```

Version là bất biến.

Không sửa đổi.

Chỉ tạo mới.

---

## Object Reference Model

Business Service không lưu Blob.

Business Service chỉ lưu:

```text
object_id
```

Ví dụ:

```text
Post

image_object_id
```

Hoặc:

```text
Product

image_object_id
```

Data Service là chủ sở hữu thực sự của dữ liệu.

---

## Audit Model

Mọi truy cập đều phải có khả năng truy vết.

Ví dụ:

```text
READ
DOWNLOAD
UPDATE
DELETE
SHARE
RESTORE
```

Audit cần ghi nhận:

```text
actor_identity_id
actor_subject_type
action
object_id
timestamp
```

---

## Data Lifecycle

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

## Multi-Tenant

Tenant là ranh giới cô lập dữ liệu.

Ví dụ:

```text
tenant = null
```

Hệ sinh thái mặc định của Platform.

Hoặc:

```text
tenant = COMPANY_B
```

Khách hàng thuê nền tảng.

Tenant không phải Subject.

Tenant không sở hữu dữ liệu.

Tenant chỉ là Isolation Boundary.

---

## Kiến trúc phân tán — Tổng kết

| Nguyên tắc                     | Mô tả                                |
| ------------------------------ | ------------------------------------ |
| Distributed First              | Thiết kế cho hệ phân tán ngay từ đầu |
| Subject Ownership              | Dữ liệu thuộc về Subject             |
| Application as Subject         | Application là Subject hợp lệ        |
| Runtime-Service Separation     | Tách Subject khỏi Runtime Service    |
| Identity-Centric Placement     | Placement dựa trên Identity          |
| Shared-Nothing Architecture    | Mỗi Shard độc lập                    |
| Capability-Based Authorization | Quyền theo Capability                |
| Tenant Isolation               | Tenant là ranh giới cô lập           |
| Horizontally Scalable          | Scale bằng cách thêm Shard           |
| Auditability                   | Mọi hành động đều truy vết được      |
