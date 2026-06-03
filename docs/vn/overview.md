# Tổng quan

[English](../en/overview.md) | **Tiếng Việt**

---

## Data Service là gì?

Data Service là **hạ tầng dữ liệu phân tán** của Xime Base Platform.

Vai trò của nó là cung cấp một tầng thống nhất, nhất quán cho việc lưu trữ, truy cập và quản lý bất kỳ dữ liệu nhị phân nào trên toàn nền tảng — mà không cần biết dữ liệu đó có ý nghĩa gì trong nghiệp vụ.

```
Application Services
  post-service     → lưu post_image_object_id
  product-service  → lưu product_image_object_id
  chat-service     → lưu attachment_object_id
         ↓  (tất cả dùng object_id để tham chiếu)
    Data Service   ← sở hữu dữ liệu thực tế
         ↓
  PostgreSQL  +  Local Disk
```

---

## Vị trí trong Base Platform

Xime Base Platform được chia làm hai tầng:

### Base Platform (service lõi)

Các service chung, tái sử dụng được, độc lập với nghiệp vụ — viết một lần, dùng cho mọi ứng dụng:

| Service | Vai trò |
|---|---|
| `trust-service` | Trust infrastructure — CA, mTLS, JWT signing key |
| `identity-service` | Authentication — cấp JWT, refresh token |
| `user-service` | Human Identity Domain — credential, profile |
| `data-service` | **Data infrastructure — service này** |
| `notification-service` | Gửi thông báo |
| `payment-service` | Thanh toán |

### Application Layer (business service)

Logic nghiệp vụ của từng ứng dụng cụ thể, dùng Base Platform làm nền tảng:

- **Mạng xã hội**: post-service, comment-service, media-service
- **Thương mại điện tử**: product-service, order-service
- **SaaS / AI**: workspace-service, dataset-service, ai-agent-service

Data Service phục vụ tất cả mà không cần biết gì về domain của chúng.

---

## Triết lý thiết kế

| Câu hỏi | Trả lời |
|---|---|
| Data Service là gì? | Hạ tầng dữ liệu |
| Nó lưu gì? | Bất kỳ binary object — ảnh, video, tài liệu, dataset, AI artifact |
| Ai là owner? | Luôn là `identity_id` (không phải user, profile hay business entity) |
| Nó có biết business context không? | Không — chỉ biết ownership, storage, permission và lifecycle |
| Nó gọi service domain khác không? | Không — chỉ tích hợp với `identity-service` (JWT) và `trust-service` (mTLS) |

---

## Khái niệm cốt lõi

### Mọi thứ đều là DataObject

Không có bảng chuyên biệt cho `image`, `video` hay `document`. Mọi dữ liệu đều là `DataObject` với trường `type`. Application service quyết định ý nghĩa nghiệp vụ; Data Service chỉ lưu trữ và phục vụ.

### Ownership theo Identity

Mọi object đều có owner. Owner luôn là `identity_id`. Điều này khiến Data Service hoạt động tốt với mọi loại subject: người dùng, bot, AI agent, service account.

### Immutable Data Placement

Khi object được tạo, nó được gán vào một shard dựa trên `identity_id` của owner. Việc gán này là vĩnh viễn — object không bao giờ chuyển sang shard khác.

```
identity_id → hash → partition → DATA_SHARD_XX  (cố định mãi mãi)
```

### Phân quyền theo Capability

Quyền truy cập vào một object được quản lý bởi Access Control List (ACL). Mỗi mục trong ACL gán một role cho một identity. Role ánh xạ tới tập capability.

```
READ, WRITE, DELETE, SHARE, DOWNLOAD
```

### Tách Metadata và Blob

Database chỉ lưu metadata và storage pointer. Nội dung nhị phân thực tế nằm trên disk và được serve qua FastAPI với kiểm tra auth trên mỗi request.

---

## Data Service KHÔNG làm gì

- Không phải social post service — application service giữ business context
- Không phải CDN — blob serving là trực tiếp có auth, chưa tối ưu cho phân phối công khai
- Không phải image processing service — biến đổi và resize là vấn đề của application
- Không phải search service — nó dùng mô hình routing deterministic, không phải full-text search

---

## Ứng dụng tham chiếu cho XIME Framework

Data Service là **ứng dụng production đầu tiên được xây dựng bằng XIME Framework**. Điều này phục vụ hai mục đích:

1. **Kiểm tra thực tế** — chứng minh framework hoạt động đầu cuối trong một service thực
2. **Triển khai tham chiếu** — minh họa best practice cho việc xây dựng service với XIME: hexagonal architecture, constructor injection, explicit binding, port/adapter pattern

Các bài học từ việc xây dựng Data Service trực tiếp ảnh hưởng đến thiết kế của XIME Framework.
