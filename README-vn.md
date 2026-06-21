# Data Service

[English](README.md) | **Tiếng Việt**

> Hạ tầng dữ liệu phân tán cho Xime Base Platform — quản lý object storage, phân quyền theo capability, định tuyến theo shard và vòng đời dữ liệu.

> 🔒 **Lưu ý phiên bản.** Đây là **bản công khai phục vụ tham khảo / học tập** và sẽ **sớm ngừng được cập nhật**. Việc phát triển tiếp tục ở một **bản private dùng cho mục đích kinh doanh**, gồm các tính năng nâng cao không công bố tại đây. Sơ lược, bản private bổ sung: mã hóa dữ liệu riêng tư nhiều mức (hướng tới mã hóa đầu cuối), một hạ tầng quản lý khóa riêng, và một engine hiệu năng cao cho xử lý dữ liệu nặng. Chi tiết kỹ thuật của các tính năng này **không** nằm trong bản công khai này.

---

Data Service là một trong các service lõi của **Xime Base Platform**. Nó cung cấp tầng hạ tầng dữ liệu chung, tái sử dụng được cho mọi ứng dụng xây dựng trên nền tảng — mà không cần biết gì về business domain.

Đây cũng là **ứng dụng thực tế đầu tiên được xây dựng bằng [XIME Framework](https://github.com/nguyen-huu-thang/xime-framework)**, phục vụ như một bài kiểm tra thực tế của framework trong bối cảnh microservice production.

```
Application Services (mạng xã hội, thương mại điện tử, SaaS, AI)
               ↓ lưu / lấy qua object_id
          Data Service       ← quản lý storage, permission, lifecycle
               ↓
      PostgreSQL + Local Disk
```

---

## Data Service làm gì

Mọi dữ liệu trong hệ thống đều là `DataObject` — ảnh, video, tài liệu, dataset, AI artifact, attachment.

Data Service chịu trách nhiệm:

- **Object storage** — tải lên, phục vụ và xóa nội dung nhị phân (blob)
- **Quản lý metadata** — loại object, visibility, trạng thái, versioning
- **Phân quyền theo capability** — READ, WRITE, DELETE, SHARE, DOWNLOAD theo từng identity
- **Định tuyến shard cố định** — shard do placement cấp lúc tạo (theo dung lượng & tải), lưu cùng bản ghi và mang theo khi route, mãi mãi không đổi
- **Vòng đời dữ liệu** — ACTIVE → ARCHIVED → SOFT_DELETED → PURGED
- **Audit trail** — ghi nhận mọi thao tác đọc, ghi, chia sẻ, xóa
- **Cô lập multi-tenant** — context dữ liệu độc lập theo tenant

## Data Service KHÔNG làm gì

- Không biết object là "ảnh đại diện" hay "ảnh sản phẩm" — đó là trách nhiệm của application service
- Không gọi `user-service` hay `profile-service` — chỉ biết `identity_id`
- Không triển khai quy trình nghiệp vụ — nó là hạ tầng thuần túy

---

## Quyết định thiết kế quan trọng

### Ownership theo Identity

Mọi object đều có owner. Owner luôn là `identity_id` — không phải user, profile hay tenant. Điều này giúp Data Service tái sử dụng được với bất kỳ loại subject nào: người dùng, bot, AI agent, service account.

### Immutable Data Placement

```
object mới → placement (dung lượng & tải) → shard_id → lưu cùng bản ghi  (cố định mãi mãi)
```

Khi object được tạo trong shard `DATA_SHARD_07`, nó ở đó vĩnh viễn. Địa chỉ shard đi kèm bản ghi/tham chiếu, không tính lại từ `identity_id`. Không có cross-shard migration.

### Tách Metadata và Blob

```
PostgreSQL  ←  metadata object (id, owner, permission, status, storage_pointer)
Local Disk  ←  nội dung nhị phân (serve qua FastAPI với kiểm tra auth)
```

Database chỉ lưu `storage_pointer` (đường dẫn file tương đối), không bao giờ lưu nội dung nhị phân.

### Phân quyền theo Capability

```
JWT → identity_id → load ACL → evaluate capability → ALLOW / DENY
```

Capability: `READ`, `WRITE`, `DELETE`, `SHARE`, `DOWNLOAD`  
Role: `OWNER`, `EDITOR`, `CONTRIBUTOR`, `VIEWER`

---

## Chạy nhanh

```bash
python -m app.main
```

---

## Kiến trúc

Data Service theo **Hexagonal Architecture** (Ports and Adapters) trên nền XIME Framework:

```
app/
├── api/              ← Adapter layer (REST, gRPC handler)
├── application/      ← Use case, port, DTO
├── domain/           ← Domain model thuần túy (DataObject, ObjectPermission, ...)
├── infrastructure/   ← SQLAlchemy repository, local disk storage adapter
├── integration/      ← Identity Service client, Trust Service key sync
└── config/           ← XIME DI binding, routing, security config
```

XIME Framework xử lý dependency injection tự động từ type hint của constructor — không annotation, không decorator, không wire thủ công.

---

## Tài liệu

| Tài liệu | Mô tả |
|---|---|
| [Tổng quan](docs/vn/overview.md) | Vai trò, ranh giới và vị trí trong Base Platform |
| [Kiến trúc](docs/vn/architecture.md) | Cấu trúc tầng, XIME DI, cây thư mục |
| [Data Model](docs/vn/data-model.md) | Mô hình DataObject, schema database |
| [Phân quyền](docs/vn/authorization.md) | Capability-based ACL, role model, luồng xác thực |
| [Storage](docs/vn/storage.md) | Tách metadata và blob, local disk storage |
| [Tích hợp](docs/vn/integration.md) | Identity Service, Trust Service, JWT verification |

---

## Các Service trong Base Platform

| Service | Vai trò |
|---|---|
| `trust-service` | Trust infrastructure — CA, mTLS, JWT signing key |
| `identity-service` | Authentication infrastructure — JWT, refresh token |
| `user-service` | Human Identity Domain Service |
| `data-service` | **Data infrastructure** — object storage, permission |
| `notification-service` | Gửi thông báo |
| `payment-service` | Thanh toán |

---

## XIME Framework

Data Service là **ứng dụng tham chiếu** của XIME Framework. Nó minh họa:

- Constructor injection với port kiểu `Protocol`
- Directory-driven DI với package scanning tường minh
- Fail-fast startup validation
- Quản lý transaction tường minh
- Hexagonal architecture ở quy mô production

→ [XIME Framework](../xime%20framework/README-vn.md)

---

## Trạng thái dự án

Bản công khai này đã hoàn thành 14 phase triển khai — domain layer, persistence, authorization, API adapter, JWT verification, testing và Trust Service integration (mTLS, bootstrap certificate, key sync, scheduler) — và được công bố như một bản tham chiếu cho XIME Framework.

Repo sẽ **sớm ngừng được cập nhật**: việc phát triển tiếp tục ở bản private dùng cho kinh doanh (xem lưu ý phiên bản ở đầu trang).

---

## Giấy phép

MIT
