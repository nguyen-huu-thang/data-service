# Kiến trúc Tổng thể — Base Platform

## Mục tiêu hệ thống

Xây dựng một **Backend Platform dạng Microservice** với mục tiêu:

- Nền tảng backend dùng chung cho nhiều ứng dụng
- Tránh lặp lại các chức năng phổ biến
- Hỗ trợ scale theo chiều ngang (horizontal scaling)
- Hỗ trợ kiến trúc phân tán quy mô lớn
- Hỗ trợ multi-tenant / multi-application
- Cho phép tách riêng dữ liệu và hạ tầng cho từng tenant khi cần

---

## Hai tầng kiến trúc

### 1. Base Platform

Tập hợp các service lõi dùng chung — viết một lần, dùng lại cho nhiều ứng dụng, độc lập nghiệp vụ cụ thể:

| Service | Vai trò |
|---|---|
| `trust-service` | Trust infrastructure — CA, mTLS, JWT signing key |
| `identity-service` | Authentication infrastructure — JWT, refresh token |
| `user-service` | Human Identity Domain Service |
| `payment-service` | Thanh toán |
| `notification-service` | Thông báo |
| `data-service` | Data infrastructure — object storage, permission |
| `search-service` | Distributed lookup, shard routing |
| `analytics-service` | Phân tích dữ liệu |

### 2. Application Layer

Logic nghiệp vụ của từng ứng dụng cụ thể, sử dụng lại Base Platform:

- **Social Network**: post-service, comment-service, like-service, chat-service
- **Ecommerce**: product-service, order-service, cart-service, inventory-service
- **SaaS / AI**: workspace-service, ai-agent-service, dataset-service, billing-service

---

## Công nghệ

### Backend

| Ngôn ngữ | Dùng cho |
|---|---|
| **Python (FastAPI + Xime)** | IO-bound services, async workloads, AI/data processing — data-service, notification-service, search-service, analytics-service |
| **Java (Spring Boot)** | Transaction-heavy, security-critical, consistency-sensitive — trust-service, identity-service, user-service, payment-service |
| **Golang** (tương lai) | Realtime, streaming, video/media |

### Frontend
- React (hiện tại)
- NextJS, React Native (dự kiến)

---

## Thiết kế ID

### Binary ID
Dùng cho entity trong database, tối ưu storage và indexing.

| Dùng cho | Cấu trúc | Kích thước |
|---|---|---|
| Trust Service | 4 bytes timestamp + 16 bytes random | 20 bytes |
| Các service khác | 4 bytes timestamp + 20 bytes random | 24 bytes |

### String ID
Dùng cho đối tượng mà con người thao tác thường xuyên.

- **Service ID**: Base62, chữ thường + số — VD: `user-service`, `identity-service`
- **Tenant Service ID**: VD: `user-service-001`, `user-service-companyabc`
- **Shard ID**: Base62, chữ IN HOA + số — VD: `A0B1C2`, `EU02`, `VN01`

---

## Nguyên tắc Sharding

| Nguyên tắc | Mô tả |
|---|---|
| Shared-nothing | Mỗi shard có database riêng |
| Immutable placement | Dữ liệu gán cố định vào shard từ đầu |
| Direct routing | Route trực tiếp từ shard_id, không cần global lookup |
| Shard growth | Khi data tăng → thêm shard mới |

Mỗi shard có hai ngưỡng:
- **Soft Limit**: khuyến nghị tạo shard mới
- **Hard Limit**: shard chuyển sang read-only, không cho ghi thêm

---

## Định vị và truy xuất dữ liệu

### Direct Routing (trường hợp đã biết vị trí)
Mỗi bản ghi lưu `service_id`, `shard_id`, `network_location`. Request route trực tiếp → giảm latency.

### Search / Discovery (trường hợp chưa biết vị trí)
Dùng **Search Service** — chỉ để tìm địa chỉ dữ liệu, **không phải source of truth**. Địa chỉ thực sự của dữ liệu là bất biến (immutable placement).

---

## Multi-Tenant

```
tenant = null    → service mặc định của platform
tenant = <id>    → service riêng của tenant
```

Tenant-specific services vẫn có thể scale bằng sharding.

---

## Trust Service — Đặc điểm riêng

Trust Service được thiết kế khác biệt:
- Chỉ có một instance logic chính
- Không yêu cầu realtime dependency từ các service khác
- Nếu Trust Service ngừng hoạt động dài hạn (1-2 tháng) → các service khác vẫn hoạt động bình thường (dùng cached key/cert)

Lợi ích: giảm coupling, tăng resilience, tránh single-point runtime dependency.

---

## Định hướng kiến trúc

Hệ thống theo các nguyên tắc: distributed-first, shared-nothing, horizontally scalable, service-oriented, tenant-aware, failure-tolerant, loosely coupled.

Mục tiêu dài hạn: Backend Platform phục vụ social systems, realtime systems, ecommerce, SaaS platforms, AI infrastructure, large-scale distributed applications.
