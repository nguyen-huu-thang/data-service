# Mô hình Subject & định danh - góc nhìn Data Service

> Chốt thiết kế **2026-06-12** (trao đổi với chủ dự án). Bản đầy đủ toàn platform:
> `D:\code\xime\giới thiệu\.claude\docs\cross-cutting\mo-hinh-subject-va-dinh-danh.md`.
> Tài liệu này tóm tắt phần Data Service **phải biết và phải implement**.

---

## SubjectType chuẩn toàn platform

```text
HUMAN · BOT · AI_AGENT · APPLICATION
```

**SERVICE không bao giờ là Subject** - không xuất hiện trong `sub` của JWT, không sở hữu dữ liệu, chỉ hành động thay mặt Subject. Danh tính service chỉ sống ở tầng cert mTLS.

---

## Owner service của từng Subject

```text
subject_type      Owner service             Cơ chế xác thực                  JWT?
HUMAN          →  user-service              credential qua Identity          Có
BOT, AI_AGENT  →  agent-service             credential (API key) qua Identity Có
APPLICATION    →  application-service       cert (Trust) + cache sync        KHÔNG
```

`agent-service` là tên chốt thay cho `bot-service` trong tài liệu cũ (bao trùm bot, AI agent, robot phần cứng).

---

## APPLICATION không dùng JWT

Mỗi Application (Xime Social, Xime Chat...) gồm nhiều service con. Tất cả service con dùng chung **một** app identity (24 byte) khi thao tác dữ liệu:

* Trust khắc `owner_app_identity_id` (24 byte) vào **cert** của service con (entry SAN thứ hai, cạnh `service_id`).
* Service thuộc Base Platform không có trường này (nullable).
* Data Service đọc app identity **trực tiếp từ cert đã verify** - không cần JWT, không cần gọi service nào.

Nguyên tắc phân kênh:

```text
Cert (Trust):                        binding "service thuộc app X" - BẤT BIẾN
application-service → Data Service:  trạng thái app + System Permission - đổi nhanh,
                                     qua subject_cache + subject_permission (sync)
```

Cert sống ~100 ngày, không CRL → cert không được chứa trạng thái. Disable app phải chặn được qua subject cache trong vài phút → `subject_cache` cần thêm cột `status`.

---

## Luật resolve Subject (Data Service phải implement)

```text
Request có JWT                  → subject = JWT.sub                    (HUMAN / BOT / AI_AGENT)
Không JWT, cert có app id       → subject = cert.owner_app_identity_id (APPLICATION)
Không JWT, cert không có app id → KHÔNG có subject (chỉ endpoint hạ tầng: health, sync)
```

Quy tắc đi kèm:

* **JWT thắng khi cả hai cùng có mặt**: service xử lý request của user thì subject là user; muốn hành động nhân danh app thì gọi **không kèm JWT** - tường minh theo cấu trúc.
* **Adapter external (REST public) chỉ chấp nhận đường JWT** - không có client cert từ edge nên subject APPLICATION không thể đến từ ngoài.
* Cả hai đường resolve về cùng một model ở tầng application: `AuthenticatedSubject { identity_id, subject_type, actor_service_id?, tenant_id }`.
* **Audit ghi cặp**: subject (nhân danh ai) + actor (`service_id` từ cert - tiến trình nào). Thiết kế audit hiện tại đã có đủ hai trường này.

---

## Ảnh hưởng lên Data Service (việc phải làm)

| Hạng mục | Thay đổi |
|---|---|
| mTLS layer | Extract thêm `owner_app_identity_id` từ SAN (cạnh chỗ extract `service_id`) |
| Subject Resolution | Thêm đường resolve APPLICATION từ cert (hiện chỉ có đường JWT) |
| `subject_cache` | Thêm cột `status` - check trạng thái subject trước khi ALLOW (vd app DISABLED) |
| Subject sync | Thêm nguồn `agent-service` (BOT / AI_AGENT), cạnh user-service và application-service |
| Permission sync | Source of truth quyền hệ thống = owner service của Subject (application-service cho APPLICATION, agent-service cho BOT/AI_AGENT) |
| Adapter external | Reject mọi cơ chế subject ngoài JWT |

Cơ chế tín hiệu sync chi tiết (event push / periodic) giữa application-service và Data Service: **chưa chốt** - không chặn các phần còn lại.

---

## Điểm còn mở

* Binding gắn shard/tenant - chưa quyết (hiện tại toàn bộ tenant = null).
* Cơ chế tín hiệu sync chi tiết.
* Delegation cho agent (claim `act`, RFC 8693) - chưa thiết kế.
