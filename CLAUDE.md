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

## Việc đang chờ làm

- **Migrate sang gRPC client SDK + mTLS động - ĐÃ XONG (2026-06-13).** Theo
  [`.claude/docs/migrate-grpc-client-mtls.md`](.claude/docs/migrate-grpc-client-mtls.md).
  Đã thực hiện:
  - Sinh SDK `clients/trust/` từ `contracts/trust/key_distribution.proto`
    (`xime grpc client`) - `KeyDistributionServiceClient` + Pydantic model.
  - `TrustKeyClient` thành adapter mỏng bọc SDK (bỏ dựng channel/stub tay,
    `reset_channel`, `pre_destroy`); channel do framework quản lý.
  - `config/grpc.py`: `configure_grpc_clients("trust", KeyDistributionServiceClient)`;
    `application.yml`: thêm `grpc.clients.trust` (tls dynamic).
  - Dọn server: `TrustStartupOrchestrator` bỏ bước build server SSL;
    `CertRotationJob` rút còn `cert_sync.synchronize()` (không reload/reset tay).
  - Verify: 131 unit test xanh, `app.start()` khởi động trọn vẹn với nối dây mới.
  - **Còn 1 việc tay (chưa tự xóa theo quy tắc):** xóa file thừa
    `app/integration/trust/ssl/GrpcServerSslContextProvider.py` (đã gỡ mọi tham
    chiếu, hiện chỉ còn bị auto-scan tạo singleton vô hại). `GrpcTrustCertificateClient`
    GIỮ NGUYÊN viết tay (bootstrap chicken-egg, đúng thiết kế).
  - data-service giờ là service mẫu cho notification-service migrate theo.

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

---

## Mã lỗi & Exception

Toàn platform dùng **một chuẩn mã lỗi/exception chung** - bắt buộc đọc trước khi viết bất kỳ exception nào, đừng tự định nghĩa kiểu riêng:

`D:\code\xime\giới thiệu\.claude\docs\cross-cutting\quy-uoc-ma-loi-va-exception.md`
([link tương đối](../../giới%20thiệu/.claude/docs/cross-cutting/quy-uoc-ma-loi-va-exception.md))

- **Dải mã riêng của Data Service: `060000 - 069999`** (block 10.000). Chia 3 nhóm theo mức phơi bày (giảm dần bảo mật): **Private** `060000-063999` (lỗi nội bộ service) · **System** `064000-066999` (service khác đọc qua gRPC) · **Public** `067000-069999` (browser thấy).
- Lỗi nghiệp vụ ném 1 trong 3 base class `PrivateError`/`SystemError`/`PublicError` mang một mã trong catalog; adapter tự che lỗi theo kênh. Body REST `{errorKey, code, message}`; gRPC + metadata `xime-error`. Không để lỗi thô/stack trace lọt ra ngoài phạm vi cho phép.
- **Đã chuẩn hóa (2026-06-14), đã migrate object thuần sang domain (2026-06-15)** theo **Phụ lục B (Python)** - data-service là service mẫu Python. Cấu trúc:
  - **Object thuần (tầng domain, không phụ thuộc grpc/framework):** [`app/domain/error/`](app/domain/error/) - `Visibility.py`, `GrpcCode.py` (enum trung lập mirror tên `grpc.StatusCode`), `Channel.py`, `ErrorDef.py` (dùng `grpc_code: GrpcCode`, không `import grpc`), `error_code.py` (dict `ERROR_CODES`: common `00xxxx` + data `06xxxx`, kèm `get_error`/`generic_for`), `redaction.py` (`redact_for_channel`). Adapter gRPC map `GrpcCode -> grpc.StatusCode` bằng `grpc.StatusCode[code.name]`.
  - **Ba base class:** [`app/common/exception/AppException.py`](app/common/exception/AppException.py) - `AppException` + `PrivateError`/`SystemError`/`PublicError`. Ném lỗi bằng `raise PublicError("E067000")`; không còn exception class rời.
  - **REST:** [`app/api/rest/error_handler.py`](app/api/rest/error_handler.py) đăng ký qua `configure_exception_handlers` trong [`app/config/web.py`](app/config/web.py) (kênh `REST_EXTERNAL`).
  - **gRPC:** [`app/api/grpc/interceptor/AppExceptionInterceptor.py`](app/api/grpc/interceptor/AppExceptionInterceptor.py) đăng ký qua `configure_grpc_interceptors` trong [`app/config/grpc.py`](app/config/grpc.py) (kênh `GRPC_INTERNAL`, abort kèm metadata `xime-error`/`xime-error-code`). Chạy innermost sau interceptor built-in của framework.
  - **Đã gỡ** toàn bộ `try/except` hardcode trong controller/handler - lỗi propagate lên handler/interceptor toàn cục.
  - **Test bảo vệ chuẩn:** `test/unit/test_error_catalog.py` (không trùng mã, visibility khớp vùng số), `test/unit/test_redaction.py`, `test/unit/test_rest_error_handler.py`, `test/unit/test_grpc_error_interceptor.py`.
  - **Mã đã dùng:** Public `E067000` (object không tìm thấy) · `E067001` (object đã xóa) · `E067002` (sai trạng thái object); Private `E060000-E060002` (nội bộ/shard/blob); tái dùng common cho auth/permission/input (`E007001/2/3/4`, `E000000`).
  - **Ghi chú framework:** vài điểm gap nhỏ của Xime Framework ghi ở [`framework-notes/ghi-chu-framework.md`](framework-notes/ghi-chu-framework.md) (không chặn).

> **Chuẩn layout chung (chốt 2026-06, ghi ở mọi service để đồng bộ):** object thuần error (catalog + `Visibility`/`Channel`/`ErrorRedactor`) đặt ở **tầng domain** để giữ domain framework-neutral; ba lớp exception ở **`common/exception/`**; adapter (REST handler + gRPC interceptor) ở **`api/`**. **Tham chiếu hiện thực đầy đủ theo layout này: trust-service (Java).** data-service đã migrate xong (2026-06-15): object thuần ở `app/domain/error/`, ba lớp exception ở `app/common/exception/`, adapter ở `app/api/` - khớp chuẩn.
