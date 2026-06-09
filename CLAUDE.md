# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tổng quan

Repository này là **Data Service** — một trong các service lõi của Base Platform (Xime ecosystem).

Data Service là **distributed data infrastructure** của toàn platform: quản lý object storage, phân quyền theo capability, định tuyến theo shard, và vòng đời dữ liệu.

Data Service **không** chứa business domain — không biết "đây là ảnh đại diện" hay "đây là ảnh sản phẩm". Đó là trách nhiệm của application service.

---

## Framework & Ngôn ngữ

**Python** + **Xime Framework** (tự xây dựng):

- Xime Framework tại: `D:\code\xime\xime framework`
- CLAUDE.md của Xime Framework: `D:\code\xime\xime framework\CLAUDE.md`

**Đọc CLAUDE.md của Xime Framework trước khi viết code.**

---

## Chạy ứng dụng

```bash
python app/main.py
```

---

## Tài liệu trong .claude/

### Docs — Thiết kế & Kiến trúc

| File | Nội dung |
| --- | --- |
| [`.claude/docs/ke-hoach-trien-khai.md`](.claude/docs/ke-hoach-trien-khai.md) | **Kế hoạch triển khai** — 13 phase, thứ tự file cần tạo, checklist, dependency order |
| [`.claude/docs/thiet-ke-data-service.md`](.claude/docs/thiet-ke-data-service.md) | Thiết kế chi tiết Data Service — mô hình object, sharding, authorization, event, lifecycle |
| [`.claude/docs/thiet-ke-database.md`](.claude/docs/thiet-ke-database.md) | Database schema tham khảo — 7 bảng, index, sharding model |
| [`.claude/docs/cay-thu-muc.md`](.claude/docs/cay-thu-muc.md) | Cây thư mục dự kiến của data-service (Python + Xime) |
| [`.claude/docs/kien-truc-he-thong.md`](.claude/docs/kien-truc-he-thong.md) | Kiến trúc tổng thể Base Platform — tất cả services, công nghệ, ID design, sharding |
| [`.claude/docs/identity-service.md`](.claude/docs/identity-service.md) | Identity Service — context để tích hợp JWT và identity_id |
| [`.claude/docs/trust-service.md`](.claude/docs/trust-service.md) | Trust Service — context để verify JWT và thiết lập mTLS |
| [`.claude/docs/roadmap.md`](.claude/docs/roadmap.md) | Roadmap 7 phase — từ Core Storage đến Data Platform |
| [`.claude/docs/luong-xac-thuc.md`](.claude/docs/luong-xac-thuc.md) | Luồng xác thực — Subject model, authorization flow 4 lớp, JWT/mTLS/cache sync |
| [`.claude/docs/data-service.md`](.claude/docs/data-service.md) | Tổng quan Data Service — mục tiêu, nguyên tắc, ownership, authorization model |
| [`.claude/docs/lua-chon-cong-nghe.md`](.claude/docs/lua-chon-cong-nghe.md) | Chiến lược công nghệ — 2 giai đoạn: Python thuần → Python + xime-cryptod (C/C++) |
| [`.claude/docs/lua-chon-python.md`](.claude/docs/lua-chon-python.md) | Lý do chọn Python + Xime Framework — I/O bound, developer productivity, so sánh Go/Java |
| [`.claude/docs/ra-soat-application-layer.md`](.claude/docs/ra-soat-application-layer.md) | Rà soát application layer — use case còn thiếu, service có thể phát sinh |
| [`.claude/docs/ke-hoach-sua-code.md`](.claude/docs/ke-hoach-sua-code.md) | **Kế hoạch sửa code** — 8 phase đồng bộ code với thiết kế mới, checklist đầy đủ |
| [`.claude/docs/ke-hoach-phase-14.md`](.claude/docs/ke-hoach-phase-14.md) | **Phase 14 — Trust Integration** — mTLS, bootstrap cert, cert rotation, key persistence, schedulers |

### Rules — Quy tắc kiến trúc & Code

| File | Nội dung |
| --- | --- |
| [`.claude/rules/hexagonal-ports.md`](.claude/rules/hexagonal-ports.md) | Port/repository interface đặt ở `application/port/outbound/`, không phải `domain/` |
| [`.claude/rules/service-design.md`](.claude/rules/service-design.md) | Nguyên tắc thiết kế service trong hệ sinh thái Xime |
| [`.claude/rules/domain-coding-patterns.md`](.claude/rules/domain-coding-patterns.md) | Code patterns — immutable domain, KSUID, entity/model separation, gRPC handler |

---

## Kiến trúc cốt lõi (tóm tắt)

### DataObject — thực thể trung tâm

Mọi dữ liệu đều là `DataObject` (image, video, document, AI artifact, v.v.).

Các trường quan trọng: `object_id`, `owner_identity_id`, `tenant_id`, `shard_id` (immutable), `storage_pointer` (không lưu binary trong DB).

### Immutable Sharding

```text
owner identity_id → hash → partition → data shard (cố định mãi mãi)
```

### Authorization — Capability-Based

```text
JWT → identity_id → load ACL → evaluate capability → ALLOW / DENY
```

Capability: READ, WRITE, DELETE, SHARE, DOWNLOAD. Role: OWNER, EDITOR, VIEWER.

### Storage — Tách Metadata và Blob

- **Metadata** → PostgreSQL (object info, permission, version)
- **Blob** → Local disk filesystem — serve qua FastAPI (binary thực tế)

---

## Quy tắc code nhanh (Xime Framework)

- Constructor injection only — khai báo dependency qua type hint `__init__`
- Không dùng annotation (`@service`, `@inject`, v.v.)
- Interface dùng `Protocol`, bind tường minh trong `config/dependency.py`
- Transaction tường minh: `async with self.transaction():`
- Package excluded khỏi DI: `domain`, `dto`, `port`, `mapper`, `constants`, `exception`
- Thiếu type hint / binding / circular dependency → startup fail ngay

Chi tiết đầy đủ: `D:\code\xime\xime framework\.claude\rules\coding.md`
