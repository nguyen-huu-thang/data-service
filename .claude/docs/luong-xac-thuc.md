# Luồng xác thực — Service Interaction Flows

> Tài liệu mô tả cách các service trong Base Platform phối hợp với nhau.
>
> Tài liệu tập trung vào những gì Data Service cần biết để tích hợp đúng với Identity Service, Trust Service và Subject-based Authorization Model.

---

## 1. Login Flow

```text
Client
  POST /api/v1/auth/login
  { identifier, identifierType, credential, credentialType, userShardId? }
    │
    ▼
Identity Service
  1. Normalize identifier
  2. Resolve shard
  3. Verify credential với Subject Owner Service
       (ví dụ: user-service)
    │
    ▼
User Service
  4. Verify credential
  5. Trả về VerifiedIdentity
       {
         identity_id,
         subject_type,
         tenant_id
       }
    │
    ▼
Identity Service
  6. Generate access token
  7. Generate refresh token
  8. Sign JWT bằng signing key từ Trust Service
    │
    ▼
Client
  Nhận Access Token và Refresh Token
```

---

## 2. Subject Model

Data Service hoạt động dựa trên Subject.

Subject là bất kỳ thực thể nào có thể sở hữu dữ liệu hoặc được cấp quyền.

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

hoặc:

```text
identity_id = 01XYZ...
subject_type = APPLICATION
name = Xime Social
```

Data Service sử dụng Subject để:

* Ownership
* Authorization
* Audit
* Logging

---

## 3. Runtime Service Identity

Data Service phân biệt rõ:

## Subject Identity

Đại diện cho actor kinh doanh.

Ví dụ:

```text
HUMAN
BOT
APPLICATION
```

Được biểu diễn bằng:

```text
identity_id
subject_type
```

---

## Service Identity

Đại diện cho tiến trình runtime.

Ví dụ:

```text
post-service
feed-service
search-service
identity-service
```

Được biểu diễn bằng:

```text
service_id
certificate
shard_id
```

Được Trust Service xác thực bằng mTLS.

Cert của service thuộc Application Layer mang thêm:

```text
owner_app_identity_id
```

(24 byte - app mà service này thuộc về, dùng để resolve subject APPLICATION; service Base Platform không có trường này).

Service không sở hữu dữ liệu.

Service chỉ thực hiện hành động thay mặt Subject.

---

## 4. Request Flow vào Data Service

```text
Client / Application

↓

Data Service

Authorization:
Bearer JWT

mTLS:
Service Certificate
```

---

## Bước 1 — Verify Service Identity

Data Service xác thực:

```text
service_id
shard_id
certificate
```

thông qua mTLS.

Ví dụ:

```text
post-service
```

hoặc:

```text
feed-service
```

---

## Bước 2 — Verify JWT

```text
Extract JWT

↓

Verify Signature

↓

Validate Claims
```

Kiểm tra:

```text
exp
nbf
iss
aud
```

Ví dụ:

```text
aud = data-service
```

---

## Bước 3 — Resolve Subject

Subject được resolve theo hai đường (chốt 2026-06, xem [mo-hinh-subject-va-dinh-danh.md](mo-hinh-subject-va-dinh-danh.md)):

```text
Request có JWT                  → subject = JWT.sub                    (HUMAN / BOT / AI_AGENT)
Không JWT, cert có app id       → subject = cert.owner_app_identity_id (APPLICATION)
Không JWT, cert không có app id → KHÔNG có subject (chỉ endpoint hạ tầng: health, sync)
```

APPLICATION **không bao giờ dùng JWT** - service con của app được Trust khắc `owner_app_identity_id` vào cert (SAN); Data Service đọc trực tiếp từ cert đã verify ở Bước 1.

Quy tắc ưu tiên: JWT thắng khi cả hai cùng có mặt (service xử lý request của user thì subject là user); muốn hành động nhân danh app thì gọi **không kèm JWT**. Adapter external (REST public) chỉ chấp nhận đường JWT.

Ví dụ:

```text
identity_id = USER123   (từ JWT - HUMAN)
identity_id = APP001    (từ cert - APPLICATION)
```

Sau đó:

```text
subject_cache

↓

subject_type

↓

name
```

Ví dụ:

```text
APPLICATION

Xime Social
```

hoặc:

```text
HUMAN

Nguyen Van A
```

Kết quả:

```text
Authenticated Subject
```

Kèm check **status** từ subject_cache (vd app DISABLED → DENY) - bắt buộc với APPLICATION vì cert sống ~100 ngày, trạng thái không nằm trong cert.

---

## 5. Authorization Flow

Data Service sử dụng nhiều lớp quyền.

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

## 6. System Permission Check

Kiểm tra quyền hệ thống.

Nguồn dữ liệu:

```text
subject_permission
```

(cache cục bộ)

Ví dụ:

```text
DATA_READ_ANY
DATA_WRITE_ANY
DATA_DELETE_ANY
DATA_RESTORE_ANY
DATA_SHARE_ANY
```

---

Ví dụ:

```text
Subject:
Xime Moderation

Permission:
DATA_DELETE_ANY
```

Có thể:

```text
DELETE object
```

mà không cần là Owner.

---

Ví dụ:

```text
Subject:
Xime Backup

Permission:
DATA_READ_ANY
```

Có thể đọc toàn bộ dữ liệu.

---

## 7. Object Permission Check

Nếu Subject không có quyền hệ thống phù hợp:

```text
↓

Object Permission
```

Kiểm tra ACL:

```text
OWNER
EDITOR
VIEWER
```

Ví dụ:

```text
Object A

User A → OWNER
User B → EDITOR
Bot C  → VIEWER
```

---

## 8. Ownership Check

Nếu ACL không tồn tại:

Kiểm tra:

```text
owner_identity_id
owner_subject_type
```

Ví dụ:

```text
owner_identity_id = USER123
owner_subject_type = HUMAN
```

Nếu Subject hiện tại trùng Owner:

```text
ALLOW
```

---

## 9. Visibility Check

Kiểm tra:

```text
PRIVATE
INTERNAL
PUBLIC
```

---

## PRIVATE

Chỉ Owner hoặc Subject được cấp quyền.

---

## INTERNAL

Theo policy của Application.

---

## PUBLIC

Không yêu cầu Authorization.

---

## 10. JWT Public Key Sync Flow

Data Service không gọi Trust Service cho mỗi request.

---

## Startup

```text
Data Service

↓

Trust Service

↓

GetVerificationKeys
```

Nhận:

```text
KeyContext
```

và lưu vào:

```text
VerificationKeyCache
```

---

## Runtime

```text
JWT

↓

kid

↓

VerificationKeyCache

↓

Public Key

↓

Verify
```

---

## Cache Miss

```text
JWT

↓

Unknown kid

↓

Background Sync

↓

Trust Service

↓

Retry
```

---

## 11. Subject Cache Sync Flow

Data Service cache Subject Information.

Source of truth nằm ở Subject Owner Service.

Ví dụ:

```text
user-service          (HUMAN)
agent-service         (BOT / AI_AGENT)
application-service   (APPLICATION)
```

---

Thông tin cache:

```text
identity_id
subject_type
name
```

---

Sync bằng:

```text
Event
```

hoặc:

```text
Periodic Sync
```

---

## 12. Permission Cache Sync Flow

Data Service cache quyền hệ thống.

Source of truth nằm ở owner service của Subject:

```text
application-service   (quyền của APPLICATION)
agent-service         (quyền của BOT / AI_AGENT)
user-service          (quyền của HUMAN)
```

---

Ví dụ:

```text
Xime Social

↓

DATA_CREATE_OBJECT
DATA_READ_OBJECT
```

---

Khi quyền thay đổi:

```text
Permission Changed

↓

Data Service

↓

Update subject_permission
```

---

## 13. mTLS Setup Flow

mTLS được thiết lập khi bootstrap.

```text
Data Service

↓

Trust Service

↓

Issue Certificate

↓

Certificate Cache

↓

Outbound gRPC Calls
```

---

Certificate được dùng cho:

```text
Identity Service
User Service
Application Service
Search Service
```

---

## 14. Shard Resolution

Placement của dữ liệu dựa trên Owner Identity.

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
APP001

↓

DATA_SHARD_03
```

hoặc:

```text
USER123

↓

DATA_SHARD_07
```

Placement là bất biến.

Không thay đổi sau khi tạo.

---

## 15. Audit Flow

Mọi hành động đều phải có khả năng truy vết.

Audit lưu:

```text
actor_identity_id
actor_subject_type
actor_name
service_id
action
object_id
timestamp
```

Ví dụ:

```text
APP001

APPLICATION

Xime Social

post-service

DELETE

OBJECT_123
```

---

## Token Hierarchy

```text
Trust Service
  │
  ├── Generate Key Pair
  │
  ├── Public Key
  │
  ▼

Identity Service
  │
  ├── Sign JWT
  │
  ▼

Subject
  │
  ├── identity_id
  ├── subject_type
  └── permissions

  ▼

Data Service
  │
  ├── Verify JWT
  ├── Resolve Subject
  ├── Evaluate Permissions
  └── Execute Request
```

---

## Các điểm Data Service phải Implement

| Thành phần                   | Mô tả                          |
| ---------------------------- | ------------------------------ |
| JWT Verification             | Verify JWT từ Identity Service |
| Application Subject Resolution | Resolve subject APPLICATION từ `owner_app_identity_id` trong cert (không JWT) |
| Subject Status Check         | Check trạng thái subject từ subject cache (vd app DISABLED → DENY) |
| VerificationKeyCache         | Cache Public Key               |
| Subject Cache                | Cache Subject Information      |
| Permission Cache             | Cache System Permission        |
| mTLS Client                  | Service Authentication         |
| System Permission Evaluation | Quyền hệ thống                 |
| Object Permission Evaluation | ACL                            |
| Ownership Evaluation         | Owner Rule                     |
| Visibility Evaluation        | Public/Internal/Private        |
| Audit Trail                  | Ghi nhận mọi hành động         |
| Shard Validation             | Xác thực đúng Shard            |
| Permission Sync              | Đồng bộ quyền hệ thống         |
| Subject Sync                 | Đồng bộ Subject Metadata       |
