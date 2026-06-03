# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tổng quan

Repository này là **Data Service** — một trong các service lõi của Base Platform (Xime ecosystem).

Data Service là **distributed data infrastructure** của toàn platform: quản lý object storage, phân quyền theo capability, định tuyến theo shard, và vòng đời dữ liệu.

Data Service **không** chứa business domain — không biết "đây là ảnh đại diện" hay "đây là ảnh sản phẩm". Đó là trách nhiệm của application service.

**Trạng thái hiện tại:** Giai đoạn thiết kế — chỉ có tài liệu, chưa có code Python.

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
| [`.claude/docs/roadmap.md`](.claude/docs/roadmap.md) | Các điểm cần hoàn thiện trong tương lai (chưa triển khai) |
| [`.claude/docs/luong-xac-thuc.md`](.claude/docs/luong-xac-thuc.md) | Luồng xác thực giữa các service — JWT verification, mTLS, shard routing |

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
