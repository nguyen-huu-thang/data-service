# Nguyên tắc thiết kế Service trong hệ sinh thái Xime

## Nguyên tắc chung (áp dụng cho mọi service trong Base Platform)

Các nguyên tắc này rút ra từ kinh nghiệm thiết kế user-service, identity-service và data-service. Áp dụng khi xây dựng Data Service.

---

## 1. Service phải có boundary rõ ràng

Data Service là **data infrastructure** — không phải social service, business service, hay media processing service.

Khi có tính năng mới, luôn hỏi: "Tính năng này thuộc data infrastructure hay thuộc application service?"

Ví dụ:
- Lưu file và cấp quyền truy cập → Data Service ✓
- Biết "đây là ảnh đại diện của user" → Application Service ✓ (Data Service chỉ lưu object_id)

---

## 2. Không phụ thuộc vào domain service khác

Data Service chỉ biết `identity_id` — không gọi user-service hay profile-service để lấy thêm thông tin.

Thiết kế này giúp:
- Reusable cho mọi loại subject (human, bot, service, AI agent)
- Không bị coupling với business domain
- Scale độc lập

---

## 3. Immutable placement — không bao giờ đổi shard

Khi object được tạo trong shard X → mãi mãi thuộc shard X.

Không thiết kế tính năng migration object giữa shard — đây là nguyên tắc nền tảng của kiến trúc.

---

## 4. Deterministic routing — không search toàn cluster

Routing phải luôn:
```
identity_id → hash → shard → direct route
```

Không broadcast query toàn cluster. Search Service chỉ dùng để resolve location, không phải source of truth.

---

## 5. Identifier phải normalize trước khi hash

Bất kỳ giá trị nào dùng để routing đều phải normalize:

```
email: TEST@MAIL.COM → test@mail.com
phone: +84 123 456 789 → 84123456789
```

Nếu không normalize → routing sai, duplicate.

---

## 6. Locality — dữ liệu liên quan phải cùng shard

Data object, permission, version của cùng một object nên nằm cùng shard (chúng đã ở cùng shard vì theo owner identity_id).

Tối thiểu hóa cross-shard call trong single request.

---

## 7. Không lưu binary trong database

Database chỉ lưu metadata và `storage_pointer`. Binary file lưu trên local disk, serve qua FastAPI với kiểm tra quyền trên từng request.

Điều này giúp database nhỏ, scale dễ, backup dễ, đổi storage backend dễ.

---

## 8. Audit là bắt buộc

Mọi thao tác đọc/ghi/xóa/chia sẻ dữ liệu đều phải có audit trail.

Audit có thể lưu trong bảng `object_audit` local hoặc gửi sang audit-service riêng sau.

---

## 9. Multi-credential / multi-subject (tương tự user-service)

Không hardcode loại subject. Data Service phục vụ bất kỳ `identity_id` nào — human, bot, service, AI agent.

Tương tự user-service không hardcode credential type:

```
user:
  credential:
    PASSWORD, GOOGLE_OAUTH, PASSKEY, MFA
```

Data Service không hardcode object type — IMAGE, VIDEO, DOCUMENT, DATASET đều là `DataObject`.

---

## 10. Service không được tin client

Internal API của Data Service chỉ nhận request từ authenticated service qua mTLS.

Luôn verify:
- JWT signature (dùng public key từ Trust Service)
- Service certificate (nếu internal call)

Không có public endpoint trực tiếp cho write operations mà không qua authentication layer.

---

## 11. Ưu tiên đơn giản trước

Không triển khai kiến trúc phức tạp (event sourcing, CQRS đầy đủ, distributed saga) khi chưa thực sự cần.

Ưu tiên:
1. Core service ổn định
2. Service boundary rõ ràng
3. Maintainability
4. Observability cơ bản
5. Scalability hợp lý

Tham khảo thêm: `.claude/docs/roadmap.md`
