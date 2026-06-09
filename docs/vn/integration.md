# Tích hợp

[English](../en/integration.md) | **Tiếng Việt**

---

## Tổng quan

Data Service tích hợp với hai service khác trong Base Platform:

| Service | Mục đích tích hợp |
|---|---|
| `trust-service` | Lấy JWT public key để xác minh token; certificate mTLS cho service-to-service authentication |
| `identity-service` | Trích xuất và xác thực `identity_id` từ JWT token trên mỗi request |

Data Service **không** gọi `user-service`, `profile-service` hay bất kỳ application service nào. Nó được cố tình cách ly khỏi business domain.

---

## Trust Service

Trust Service quản lý hai hệ thống độc lập:

1. **JWT Key System** — cung cấp public key để xác minh JWT access token
2. **Service Trust System** — quản lý certificate mTLS cho service-to-service communication

### Đồng bộ JWT Public Key

Data Service không gọi Trust Service trên mỗi request. Thay vào đó, nó duy trì cache local các public key được làm mới định kỳ:

```
Data Service khởi động
      ↓
Lấy public key từ Trust Service (GetPublicKeys RPC)
      ↓
Cache key trong memory (VerificationKeyCache)
      ↓
Xác minh JWT token đến cục bộ — không có network call mỗi request
      ↓
Làm mới định kỳ (trước khi key hết hạn)
```

Thiết kế này đảm bảo Trust Service không ảnh hưởng đến latency request. Ngay cả khi Trust Service tạm thời không khả dụng, Data Service vẫn tiếp tục xử lý request bằng key đã cache.

### Thiết lập mTLS

Internal service-to-service call (VD: Data Service gọi Trust Service để refresh key) dùng mutual TLS:

```
Data Service khởi động
      ↓
Yêu cầu certificate từ Trust Service (RotateCertificate RPC)
      ↓
Lưu certificate cục bộ
      ↓
Dùng certificate cho tất cả outbound internal call
      ↓
Làm mới certificate trước khi hết hạn
```

### Vị trí code tích hợp

```
app/integration/trust/
├── bootstrap/                              ← đọc bootstrap payload lúc khởi động
├── certificate/
│   ├── GrpcTrustCertificateClient.py       ← gRPC client lấy certificate từ Trust Service
│   ├── TrustCertificateResolver.py         ← resolve certificate hiện tại
│   └── TrustCertificateSynchronizer.py     ← đồng bộ và lưu certificate mới
├── key/
│   ├── TrustKeyClient.py                   ← lấy JWT public key từ Trust Service
│   ├── VerificationKeyCache.py             ← cache public key trong memory
│   ├── TrustKeyCleanup.py                  ← dọn dẹp key hết hạn
│   └── VerificationKeySynchronizer.py      ← đồng bộ key định kỳ
├── publicca/                               ← quản lý Root CA certificate
├── scheduler/                              ← job định kỳ: cert rotation, key refresh, cleanup
├── ssl/                                    ← thiết lập SSL context cho gRPC server
└── startup/                                ← orchestration khởi động toàn bộ Trust integration
```

---

## Identity Service

Identity Service cấp JWT access token cho các subject đã xác thực. Data Service tiêu thụ các token này để xác định identity yêu cầu trên mỗi inbound request.

### JWT Token Claims

JWT được Identity Service cấp chứa:

```json
{
  "sub": "<identity_id dạng hex>",
  "iss": "identity-service",
  "aud": ["data-service", "user-service", ...],
  "iat": 1700000000,
  "exp": 1700003600,
  "tid": "<tenant_id>"
}
```

Data Service sử dụng:
- `sub` → `identity_id` (owner/người yêu cầu)
- `aud` → xác nhận token được cấp cho service này
- `exp` → xác nhận token chưa hết hạn
- `tid` → tenant context

### Luồng Xác Minh JWT

```
Inbound HTTP/gRPC request
      ↓
Lấy Bearer token từ Authorization header
      ↓
Decode JWT header → lấy key ID (kid)
      ↓
Tra public key trong VerificationKeyCache
      ↓
Xác minh chữ ký dùng RSA/ECDSA public key
      ↓
Validate claims: aud, exp, iss
      ↓
Lấy identity_id từ claim 'sub'
      ↓
Set identity vào SecurityContext (XIME)
      ↓
Tiếp tục xử lý use case với identity_id đã xác minh
```

Tất cả xác minh xảy ra cục bộ bằng public key đã cache — không gọi Identity Service mỗi request.

### Vị trí code tích hợp

```
app/integration/identity/
├── client/
│   └── IdentityJwtVerifier.py     ← xác minh JWT, trích xuất identity_id
├── contract/
│   └── IdentityClaims.py          ← dataclass JWT claims
└── resolver/
    └── IdentityResolver.py        ← resolve identity context từ request
```

---

## Security Context trong XIME

XIME Framework cung cấp `SecurityContext` được điền bởi authentication middleware. Use case đọc thông tin identity từ context mà không đụng vào HTTP header trực tiếp:

```python
class CreateObjectUseCase:
    def __init__(
        self,
        security_context: SecurityContext,
        save_object_port: SaveObjectPort,
        ...
    ) -> None: ...

    async def execute(self, command: CreateObjectCommand) -> DataObject:
        identity_id = self.security_context.current_identity_id()
        # ... tạo object với identity_id làm owner
```

---

## Không Phụ Thuộc Runtime vào Trust hay Identity Service

Cả hai tích hợp đều được thiết kế sao cho **xử lý request không bao giờ bị block bởi external service call**:

- Xác minh JWT dùng key cache cục bộ (làm mới ngầm ở background)
- Certificate mTLS được cache cục bộ
- Nếu Trust Service ngừng hoạt động, Data Service vẫn tiếp tục với key đã cache cho đến khi hết hạn

Điều này tuân theo nguyên tắc của Base Platform: Trust Service có thể không khả dụng nhiều ngày mà không ảnh hưởng đến request handling của các service khác.

---

## Tóm tắt Xác Thực Request

```
Client Request
      │
      ├─ gRPC internal call (từ service khác trong Base Platform)
      │       └─ xác minh certificate mTLS
      │
      └─ REST / gRPC external call (từ application service)
              └─ xác minh JWT (cục bộ, dùng public key đã cache)
                      └─ trích xuất identity_id → set vào SecurityContext
```
