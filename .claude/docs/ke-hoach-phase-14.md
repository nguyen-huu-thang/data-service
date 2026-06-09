# Kế hoạch Phase 14 — Trust Integration: mTLS + Cert Management

> Phase này bổ sung đầy đủ tích hợp Trust Service cho Data Service:
> bootstrap cert, cert rotation định kỳ, mTLS cho gRPC, và key persistence.
>
> Tham khảo code Java tại:
> - `D:\code\xime\Base Platform\identity\src\main\java\vn\xime\identity\integration\trust`
> - `D:\code\xime\Base Platform\user\src\main\java\vn\xime\user\integration\trust`
>
> Model tham khảo chính là **user-service** (không có signing key, chỉ verify).

---

## Trạng thái tổng quan

| Bước | Tên | Trạng thái |
|---|---|---|
| 14.1 | Domain Models | ✅ Hoàn tất |
| 14.2 | Port Interfaces | ✅ Hoàn tất |
| 14.3 | DB Entities & Migration | ✅ Hoàn tất |
| 14.4 | Repositories | ✅ Hoàn tất |
| 14.5 | Root CA Certificate | ✅ Hoàn tất |
| 14.6 | Bootstrap | ✅ Hoàn tất |
| 14.7 | Cert gRPC Client + Proto | ✅ Hoàn tất |
| 14.8 | Certificate Resolver & Synchronizer | ✅ Hoàn tất |
| 14.9 | SSL Context | ✅ Hoàn tất |
| 14.10 | Update TrustKeyClient (insecure → mTLS) | ✅ Hoàn tất |
| 14.11 | Key Persistence & Synchronizer | ✅ Hoàn tất |
| 14.12 | Schedulers | ✅ Hoàn tất |
| 14.13 | Config & DI Update | ✅ Hoàn tất |

---

## Bối cảnh hiện tại

### Đã có sẵn

- `app/integration/trust/key/TrustKeyClient.py` — gọi Trust Service lấy public key, nhưng đang dùng **insecure channel** (TODO placeholder)
- `app/integration/trust/key/VerificationKeyCache.py` — in-memory cache
- `app/application/service/authorization/JwtVerificationService.py` — verify JWT từ cache

### Còn thiếu hoàn toàn

1. Bootstrap cert — đọc file bootstrap khi khởi động lần đầu
2. Certificate DB entity — lưu cert vào DB để dùng khi Trust Service mất
3. Cert rotation — tự động rotate cert định kỳ qua gRPC
4. Root CA cert — load CA cert từ file để xác minh Trust Service
5. mTLS SSL context — build context cho cả gRPC server lẫn client
6. Key persistence — lưu verification key vào DB (fallback khi Trust offline)
7. Schedulers — tự động chạy định kỳ

---

## Phạm vi của Data Service (so với Identity)

Data Service **chỉ verify JWT**, không ký — nên đơn giản hơn identity service:

| Tính năng | Identity | User | Data |
|---|---|---|---|
| Signing keys | ✅ | ❌ | ❌ |
| Verification keys | ✅ | ✅ | **✅** |
| Bootstrap cert | ✅ | ✅ | **✅** |
| Cert rotation | ✅ | ✅ | **✅** |
| mTLS client | ✅ | ✅ | **✅** |
| mTLS server | ✅ | ✅ | **✅** |

---

## Thứ tự phụ thuộc

```
14.1 Domain models
  └─ 14.2 Port interfaces
       └─ 14.3 DB entities + migration
            └─ 14.4 Repositories
                 ├─ 14.5 Root CA cert (đọc file PEM)
                 │    └─ 14.6 Bootstrap (đọc file → rotate → xóa)
                 │         └─ 14.7 Cert gRPC client + proto
                 │              └─ 14.8 CertificateResolver + Synchronizer
                 │                   └─ 14.9 SSL context (cert + CA cert)
                 │                        └─ 14.10 Update TrustKeyClient
                 │                             └─ 14.11 Key Persistence + Synchronizer
                 │                                  └─ 14.12 Schedulers
                 │                                       └─ 14.13 Config & DI
                 └─ (14.11 key persistence phụ thuộc 14.4)
```

---

## Startup sequence (quan trọng)

```
Application startup:
  1. TrustRootCertificateInitializer.initialize()        ← đọc CA cert file
  2. TrustCertificateSynchronizer.synchronize_on_startup()
       ← bootstrap hoặc load từ DB
       ← sau bước này TrustCertificateResolver.current() hoạt động
  3. TrustSslContextProvider & GrpcServerSslContextProvider ready
  4. VerificationKeySynchronizer.synchronize()           ← lần đầu dùng mTLS
  5. gRPC server start với mTLS credentials

  Sau đó (background):
  6. Schedulers chạy định kỳ: cert rotation, key refresh, key cleanup
```

---

## 14.1 — Domain Models

**Thư mục:** `app/domain/trust/`

- [ ] `Certificate.py`

```python
@dataclass(frozen=True)
class Certificate:
    certificate_id: str
    service_id: str
    public_cert: str       # PEM X.509
    private_key: str       # PEM PKCS#8
    refresh_token_id: str
    refresh_token: str     # one-time, bound to cert
    issued_at: datetime
    expires_at: datetime

    def needs_rotation(self, now: datetime, threshold_days: int = 150) -> bool:
        # Rotate khi đã dùng >= 150 ngày (cert thường hết hạn sau 180 ngày)
        return (now - self.issued_at).days >= threshold_days
```

- [ ] `RootCertificate.py`

```python
@dataclass(frozen=True)
class RootCertificate:
    pem: str   # CA cert PEM — dùng để verify Trust Service certificate
```

- [ ] `VerificationKeyRecord.py` — bản ghi lưu DB, khác với `KeyContext` là RAM model

```python
@dataclass(frozen=True)
class VerificationKeyRecord:
    key_id: str
    public_key: str        # PEM
    algorithm: str         # RS256, ES256, EdDSA
    activate_at: datetime
    expires_at: datetime
    is_deleted: bool

    def is_valid(self, now: datetime) -> bool:
        return not self.is_deleted and now < self.expires_at
```

### Kiểm tra 14.1

- [ ] Tất cả model dùng `@dataclass(frozen=True)`
- [ ] `Certificate.needs_rotation()` nhận `now` làm tham số (testable)
- [ ] Không có import từ `infrastructure`, `application`, `sqlalchemy`

---

## 14.2 — Port Interfaces

**Thư mục mới:** `app/application/port/outbound/trust/`

- [ ] `LoadCertificatePort.py`

```python
class LoadCertificatePort(Protocol):
    async def find_current(self) -> Certificate | None: ...
```

- [ ] `SaveCertificatePort.py`

```python
class SaveCertificatePort(Protocol):
    async def save(self, cert: Certificate) -> None: ...
    async def delete_old(self, exclude_id: str) -> None: ...
    # Xóa các cert cũ, giữ lại cert với certificate_id = exclude_id
```

- [ ] `LoadVerificationKeyPort.py`

```python
class LoadVerificationKeyPort(Protocol):
    async def find_valid(self, now: datetime) -> list[VerificationKeyRecord]: ...
```

- [ ] `SaveVerificationKeyPort.py`

```python
class SaveVerificationKeyPort(Protocol):
    async def save_all(self, keys: list[VerificationKeyRecord]) -> None: ...
    async def delete_expired(self, now: datetime) -> None: ...
```

### Kiểm tra 14.2

- [ ] Tất cả dùng `Protocol` (không phải ABC)
- [ ] Method signature có type hint đầy đủ
- [ ] Không có logic implementation

---

## 14.3 — DB Entities & Migration

- [ ] `app/infrastructure/persistence/entity/TrustCertificateEntity.py`

```python
class TrustCertificateEntity(Base):
    __tablename__ = 'trust_certificate'

    certificate_id: Mapped[str]   # VARCHAR(100) PK
    service_id: Mapped[str]       # VARCHAR(100)
    public_cert: Mapped[str]      # TEXT — PEM plain
    private_key: Mapped[str]      # TEXT — encrypted (Fernet)
    refresh_token_id: Mapped[str] # VARCHAR(100)
    refresh_token: Mapped[str]    # TEXT — encrypted (Fernet)
    issued_at: Mapped[datetime]
    expires_at: Mapped[datetime]
```

- [ ] `app/infrastructure/persistence/entity/TrustVerificationKeyEntity.py`

```python
class TrustVerificationKeyEntity(Base):
    __tablename__ = 'trust_verification_key'

    key_id: Mapped[str]         # VARCHAR(100) PK
    public_key: Mapped[str]     # TEXT — PEM plain (public key, không cần encrypt)
    algorithm: Mapped[str]      # VARCHAR(20)
    activate_at: Mapped[datetime]
    expires_at: Mapped[datetime]
    is_deleted: Mapped[bool]
```

- [ ] Alembic migration: thêm 2 bảng `trust_certificate`, `trust_verification_key`

### Kiểm tra 14.3

- [ ] Entity không có business logic
- [ ] `private_key` và `refresh_token` được đánh dấu rõ là encrypted trong comment
- [ ] Migration chạy được: `alembic upgrade head`

---

## 14.4 — Repositories

- [ ] `app/infrastructure/persistence/repository/trust/TrustCertificateRepository.py`
  - Implements `LoadCertificatePort` + `SaveCertificatePort`
  - Private key và refresh token **mã hóa Fernet** trước khi lưu, giải mã khi đọc
  - Key mã hóa đọc từ env `TRUST_CERT_ENCRYPTION_KEY` (base64-encoded 32 bytes)

- [ ] `app/infrastructure/persistence/repository/trust/TrustVerificationKeyRepository.py`
  - Implements `LoadVerificationKeyPort` + `SaveVerificationKeyPort`
  - `find_valid()` — query `WHERE is_deleted = FALSE AND expires_at > :now`
  - `delete_expired()` — hard delete `WHERE expires_at < :now`

- [ ] `app/infrastructure/persistence/mapper/TrustCertificateMapper.py`
- [ ] `app/infrastructure/persistence/mapper/TrustVerificationKeyMapper.py`

### Kiểm tra 14.4

- [ ] Repository không có business logic
- [ ] Fernet encrypt/decrypt đúng chiều: save→encrypt, load→decrypt
- [ ] `find_valid()` chỉ trả key chưa hết hạn và chưa xóa
- [ ] Mapper tách riêng khỏi repository

---

## 14.5 — Root CA Certificate

- [ ] `app/integration/trust/publicca/RootCertificateFileStore.py`
  - Đọc file PEM từ config `trust.ca_cert.path`
  - Đọc lúc startup (synchronous, không cần async)
  - Trả raw PEM string

- [ ] `app/integration/trust/publicca/TrustRootCertificateResolver.py`
  - RAM cache đơn giản: `_cert: RootCertificate | None`
  - `update(cert: RootCertificate) -> None`
  - `current() -> RootCertificate` — raise `RuntimeError` nếu chưa load

- [ ] `app/integration/trust/publicca/TrustRootCertificateInitializer.py`
  - `initialize()` — gọi `FileStore.load()` → `Resolver.update()`
  - Được gọi **đầu tiên** trong startup sequence, trước mọi thứ khác
  - Nếu file không tồn tại → raise `RuntimeError` với message rõ ràng

### Kiểm tra 14.5

- [ ] Nếu file CA cert không tồn tại → startup fail với lỗi rõ ràng
- [ ] `TrustRootCertificateResolver.current()` raise nếu chưa `initialize()`

---

## 14.6 — Bootstrap

- [ ] `app/integration/trust/bootstrap/BootstrapPayload.py`

```python
@dataclass(frozen=True)
class BootstrapCertificate:
    id: str
    service_id: str
    public_cert: str   # PEM
    private_key: str   # PEM PKCS#8
    status: str        # "ACTIVE"
    issued_at: int     # Unix milliseconds
    expires_at: int    # Unix milliseconds

@dataclass(frozen=True)
class BootstrapPayload:
    certificate: BootstrapCertificate
    token_id: str
    refresh_token: str
```

- [ ] `app/integration/trust/bootstrap/BootstrapValidator.py`

  Kiểm tra:
  - `status == "ACTIVE"`
  - `service_id` khớp với config `trust.service_id`
  - `expires_at > now` (chưa hết hạn)
  - `public_cert`, `private_key`, `token_id`, `refresh_token` không rỗng

- [ ] `app/integration/trust/bootstrap/BootstrapLoader.py`
  - `exists() -> bool` — kiểm tra file có tồn tại không
  - `load() -> BootstrapPayload` — đọc file, base64 decode, JSON parse
  - `delete() -> None` — xóa file sau khi dùng xong (one-time use)
  - Config: `trust.bootstrap.path`

### Kiểm tra 14.6

- [ ] `BootstrapLoader.load()` raise lỗi rõ ràng nếu JSON malformed
- [ ] `BootstrapValidator` fail nếu `service_id` sai (bảo vệ nhầm service)
- [ ] `BootstrapLoader.delete()` được gọi sau khi cert đã lưu DB thành công
- [ ] Nếu `delete()` fail → log error nhưng không raise (cert đã lưu rồi)

---

## 14.7 — Trust Cert gRPC Client + Proto

- [ ] `app/integration/trust/proto/trust_cert_service.proto`

  Copy từ `D:\code\xime\Base Platform\trust\src\main\proto\external\certificate.proto`, điều chỉnh package name cho Python:

  ```protobuf
  syntax = "proto3";
  package trust.v1.cert;

  service CertificateService {
    rpc RotateCertificate (RotateCertificateRequest) returns (RotateCertificateResponse);
  }

  message RotateCertificateRequest {
    string token_id      = 1;
    string refresh_token = 2;
    string private_key   = 3;
  }

  message RotateCertificateResponse {
    CertificateDto certificate      = 1;
    string service_id               = 2;
    string next_refresh_token       = 3;
    string refresh_token_id         = 4;
    int64  issued_at                = 5;
    int64  expires_at               = 6;
  }

  message CertificateDto {
    string id          = 1;
    string public_cert = 2;
    string private_key = 3;
  }
  ```

- [ ] Generate stubs:
  ```bash
  python -m grpc_tools.protoc \
      -I app/integration/trust/proto \
      --python_out=app/integration/trust/generated \
      --grpc_python_out=app/integration/trust/generated \
      app/integration/trust/proto/trust_cert_service.proto
  ```

- [ ] `app/integration/trust/certificate/GrpcTrustCertificateClient.py`
  - Constructor nhận `TrustSslContextProvider` + `RuntimeConfig`
  - Channel tạo **lazily** (sau khi SSL context sẵn sàng, không tạo trong `__init__`)
  - `rotate_certificate(token_id, refresh_token, private_key) -> RotatedCertificate`
  - `pre_destroy()` — đóng channel

### Kiểm tra 14.7

- [ ] Proto file khớp với trust service API
- [ ] Generated files không được edit tay
- [ ] Channel lazy init — không kết nối khi chưa có cert

---

## 14.8 — Certificate Resolver & Synchronizer

- [ ] `app/integration/trust/certificate/TrustCertificateResolver.py`

```python
class TrustCertificateResolver:
    def __init__(self) -> None:
        self._cert: Certificate | None = None
        self._lock = threading.Lock()

    def update(self, cert: Certificate) -> None:
        with self._lock:
            self._cert = cert

    def current(self) -> Certificate:
        # Raise RuntimeError nếu chưa load
        ...

    def current_or_none(self) -> Certificate | None:
        return self._cert
```

- [ ] `app/integration/trust/certificate/TrustCertificateSynchronizer.py`

  **Startup flow** (`synchronize_on_startup()`):

  ```
  has_bootstrap = BootstrapLoader.exists()
  has_db_cert   = LoadCertificatePort.find_current() is not None

  CASE 1 (NEW): has_bootstrap=True, has_db_cert=False
    1. payload = BootstrapLoader.load()
    2. BootstrapValidator.validate(payload)
    3. cert = Certificate từ payload (chưa rotate)
    4. SaveCertificatePort.save(cert)          ← lưu cert bootstrap vào DB
    5. Gọi GrpcTrustCertificateClient.rotate_certificate(...)  ← lấy cert mới
    6. SaveCertificatePort.save(new_cert)      ← lưu cert mới
    7. TrustCertificateResolver.update(new_cert)
    8. BootstrapLoader.delete()               ← xóa file bootstrap

  CASE 2 (ACTIVE): has_bootstrap=False, has_db_cert=True
    1. cert = LoadCertificatePort.find_current()
    2. TrustCertificateResolver.update(cert)

  CASE 3 (BROKEN): has_bootstrap=False, has_db_cert=False
    → raise RuntimeError("No cert available")

  CASE 4 (BOTH): has_bootstrap=True, has_db_cert=True
    → Ưu tiên bootstrap (fresh cert), xử lý như CASE 1
  ```

  **Periodic rotation** (`synchronize()`):

  ```
  cert = LoadCertificatePort.find_current()
  if cert.needs_rotation(now):
    new_cert = GrpcTrustCertificateClient.rotate_certificate(
        cert.refresh_token_id, cert.refresh_token, cert.private_key
    )
    SaveCertificatePort.save(new_cert)
    TrustCertificateResolver.update(new_cert)
    TrustSslContextProvider.reload()
    GrpcServerSslContextProvider.reload_if_supported()
    SaveCertificatePort.delete_old(exclude_id=new_cert.certificate_id)
  ```

### Kiểm tra 14.8

- [ ] CASE 3 → startup fail với RuntimeError rõ ràng
- [ ] Bootstrap file bị xóa **sau khi** cert đã lưu DB thành công
- [ ] Nếu rotate thất bại lúc startup → propagate exception (không swallow)
- [ ] Nếu rotate thất bại lúc periodic → log error, giữ cert hiện tại
- [ ] `TrustCertificateResolver.current()` raise nếu chưa `synchronize_on_startup()`

---

## 14.9 — SSL Context

- [ ] `app/integration/trust/ssl/TrustSslContextProvider.py`
  - Build gRPC credentials cho **outgoing requests** (client → Trust Service)
  - `get_ssl_credentials() -> grpc.ChannelCredentials` — lazy init + lock
  - `reload()` — tái build sau khi cert rotate
  - Phụ thuộc: `TrustCertificateResolver` + `TrustRootCertificateResolver`

```python
def _build(self) -> grpc.ChannelCredentials:
    cert = self._cert_resolver.current()
    ca   = self._root_ca_resolver.current()
    return grpc.ssl_channel_credentials(
        root_certificates=ca.pem.encode(),
        private_key=cert.private_key.encode(),
        certificate_chain=cert.public_cert.encode(),
    )
```

- [ ] `app/integration/trust/ssl/GrpcServerSslContextProvider.py`
  - Build gRPC credentials cho **incoming requests** (gRPC server của data service)
  - `get_server_credentials() -> grpc.ServerCredentials`
  - `reload()` — tái build sau khi cert rotate

```python
def _build(self) -> grpc.ServerCredentials:
    cert = self._cert_resolver.current()
    ca   = self._root_ca_resolver.current()
    return grpc.ssl_server_credentials(
        private_key_certificate_chain_pairs=[
            (cert.private_key.encode(), cert.public_cert.encode())
        ],
        root_certificates=ca.pem.encode(),
        require_client_auth=True,   # mutual TLS bắt buộc
    )
```

### Kiểm tra 14.9

- [ ] `get_ssl_credentials()` thread-safe (lazy init + lock)
- [ ] `reload()` được gọi sau mỗi lần cert rotate
- [ ] `require_client_auth=True` — server yêu cầu client cert (mTLS)

---

## 14.10 — Update TrustKeyClient (insecure → mTLS)

**Sửa:** `app/integration/trust/key/TrustKeyClient.py`

- [ ] Thêm dependency `ssl_context_provider: TrustSslContextProvider` vào constructor
- [ ] Đổi `grpc.aio.insecure_channel(...)` thành `grpc.aio.secure_channel(..., credentials)`

```python
# Trước:
self._channel = grpc.aio.insecure_channel(f"{host}:{port}")

# Sau:
credentials = ssl_context_provider.get_ssl_credentials()
self._channel = grpc.aio.secure_channel(f"{host}:{port}", credentials)
```

### Kiểm tra 14.10

- [ ] Không còn `insecure_channel` trong production code
- [ ] Channel được tạo sau khi `TrustSslContextProvider` đã có credentials (startup sequence)

---

## 14.11 — Key Persistence & Synchronizer

- [ ] `app/integration/trust/key/VerificationKeySynchronizer.py`

  **Logic** (`synchronize()`):

  ```
  Try:
    keys = TrustKeyClient.fetch_verification_keys("identity", service_id)
    SaveVerificationKeyPort.save_all(keys as VerificationKeyRecord)
    valid = [k for k in keys if k.is_valid(now)]
    VerificationKeyCache.update([to_key_context(k) for k in valid])
    log.info("Synced %d keys (%d valid)", len(keys), len(valid))
  Except (gRPC error / Trust Service down):
    log.warning("Trust Service unavailable — loading keys from DB")
    records = LoadVerificationKeyPort.find_valid(now)
    if not records:
        log.error("No valid verification keys in DB")
    VerificationKeyCache.update([to_key_context(r) for r in records])
  ```

- [ ] `app/integration/trust/key/TrustKeyCleanup.py`

```python
async def cleanup(self, now: datetime) -> None:
    await self._save_key_port.delete_expired(now)
    self._cache.clean_expired(now)
```

### Kiểm tra 14.11

- [ ] Khi Trust Service down → load từ DB, không raise exception
- [ ] Nếu DB cũng không có key → log error (service vẫn chạy, JWT verify sẽ fail khi không có key)
- [ ] `save_all` dùng upsert hoặc delete-then-insert (không duplicate key)

---

## 14.12 — Schedulers

**Thư mục mới:** `app/infrastructure/scheduler/`

> **Đọc Xime Framework CLAUDE.md trước** để biết cách khai báo scheduled task.

- [ ] `TrustCertificateSynchronizationScheduler.py`
  - `post_construct` → `TrustCertificateSynchronizer.synchronize_on_startup()`
  - Periodic mỗi **24 giờ** → `TrustCertificateSynchronizer.synchronize()`

- [ ] `TrustVerificationKeySynchronizationScheduler.py`
  - `post_construct` → `VerificationKeySynchronizer.synchronize()`
  - Periodic mỗi **1 giờ** trong 24h đầu, sau đó **5 ngày** một lần

- [ ] `TrustKeyCleanupScheduler.py`
  - Periodic mỗi **30 ngày** → `TrustKeyCleanup.cleanup(now)`

### Kiểm tra 14.12

- [ ] Cert scheduler chạy **trước** key scheduler (cert cần sẵn trước khi fetch key qua mTLS)
- [ ] Scheduler không raise exception ra ngoài — wrap toàn bộ trong try/except + log
- [ ] `post_construct` chạy đúng thứ tự startup sequence

---

## 14.13 — Config & DI Update

- [ ] Thêm scan paths vào `app/config/dependency.py`:

```python
dependency.scan(
    # ... (giữ nguyên các scan cũ) ...
    "app.infrastructure.scheduler",
    "app.integration.trust.bootstrap",
    "app.integration.trust.publicca",
    "app.integration.trust.certificate",
    "app.integration.trust.ssl",
)
```

- [ ] Thêm bindings mới:

```python
dependency.bind({
    # ... (giữ nguyên binding cũ) ...
    LoadCertificatePort:     TrustCertificateRepository,
    SaveCertificatePort:     TrustCertificateRepository,
    LoadVerificationKeyPort: TrustVerificationKeyRepository,
    SaveVerificationKeyPort: TrustVerificationKeyRepository,
})
```

- [ ] Thêm config env mới:

| Key | Mô tả | Ví dụ |
|---|---|---|
| `trust.bootstrap.path` | Đường dẫn bootstrap file | `/secrets/bootstrap.b64` |
| `trust.ca_cert.path` | Đường dẫn CA cert PEM | `/certs/ca.pem` |
| `trust.service_id` | ID của service này | `data-service` |
| `trust.grpc.host` | Host Trust Service | `trust-service` |
| `trust.grpc.port` | Port Trust Service | `50052` |
| `TRUST_CERT_ENCRYPTION_KEY` | Key mã hóa Fernet cho DB (base64 32 bytes) | *(env var bí mật)* |

### Kiểm tra 14.13

- [ ] `python app/main.py` khởi động không lỗi khi có đủ config
- [ ] DI resolve toàn bộ dependency mới
- [ ] Không còn `insecure_channel` nào trong code
- [ ] Startup sequence đúng thứ tự: CA cert → Bootstrap/Cert → SSL → Keys → gRPC server

---

## Tổng hợp file cần tạo mới

### Domain (3 file)

- [ ] `app/domain/trust/Certificate.py`
- [ ] `app/domain/trust/RootCertificate.py`
- [ ] `app/domain/trust/VerificationKeyRecord.py`

### Port Interfaces (4 file)

- [ ] `app/application/port/outbound/trust/LoadCertificatePort.py`
- [ ] `app/application/port/outbound/trust/SaveCertificatePort.py`
- [ ] `app/application/port/outbound/trust/LoadVerificationKeyPort.py`
- [ ] `app/application/port/outbound/trust/SaveVerificationKeyPort.py`

### Infrastructure — Entities (2 file)

- [ ] `app/infrastructure/persistence/entity/TrustCertificateEntity.py`
- [ ] `app/infrastructure/persistence/entity/TrustVerificationKeyEntity.py`

### Infrastructure — Mappers (2 file)

- [ ] `app/infrastructure/persistence/mapper/TrustCertificateMapper.py`
- [ ] `app/infrastructure/persistence/mapper/TrustVerificationKeyMapper.py`

### Infrastructure — Repositories (2 file)

- [ ] `app/infrastructure/persistence/repository/trust/TrustCertificateRepository.py`
- [ ] `app/infrastructure/persistence/repository/trust/TrustVerificationKeyRepository.py`

### Integration — Bootstrap (3 file)

- [ ] `app/integration/trust/bootstrap/BootstrapPayload.py`
- [ ] `app/integration/trust/bootstrap/BootstrapValidator.py`
- [ ] `app/integration/trust/bootstrap/BootstrapLoader.py`

### Integration — Public CA (3 file)

- [ ] `app/integration/trust/publicca/RootCertificateFileStore.py`
- [ ] `app/integration/trust/publicca/TrustRootCertificateResolver.py`
- [ ] `app/integration/trust/publicca/TrustRootCertificateInitializer.py`

### Integration — Certificate (3 file)

- [ ] `app/integration/trust/certificate/GrpcTrustCertificateClient.py`
- [ ] `app/integration/trust/certificate/TrustCertificateResolver.py`
- [ ] `app/integration/trust/certificate/TrustCertificateSynchronizer.py`

### Integration — SSL (2 file)

- [ ] `app/integration/trust/ssl/TrustSslContextProvider.py`
- [ ] `app/integration/trust/ssl/GrpcServerSslContextProvider.py`

### Integration — Key (2 file mới, 1 file sửa)

- [ ] `app/integration/trust/key/VerificationKeySynchronizer.py` *(mới)*
- [ ] `app/integration/trust/key/TrustKeyCleanup.py` *(mới)*
- [ ] `app/integration/trust/key/TrustKeyClient.py` *(sửa — insecure → mTLS)*

### Proto + Generated (3 file)

- [ ] `app/integration/trust/proto/trust_cert_service.proto`
- [ ] `app/integration/trust/generated/trust_cert_service_pb2.py` *(generated)*
- [ ] `app/integration/trust/generated/trust_cert_service_pb2_grpc.py` *(generated)*

### Schedulers (3 file)

- [ ] `app/infrastructure/scheduler/TrustCertificateSynchronizationScheduler.py`
- [ ] `app/infrastructure/scheduler/TrustVerificationKeySynchronizationScheduler.py`
- [ ] `app/infrastructure/scheduler/TrustKeyCleanupScheduler.py`

### Config & Migration (2 file sửa)

- [ ] `app/config/dependency.py` *(sửa — thêm scan + bindings)*
- [ ] Alembic migration mới *(thêm 2 bảng)*

---

## Lưu ý trước khi implement

1. **Xime Framework scheduler** — đọc `D:\code\xime\xime framework\CLAUDE.md` để biết cách khai báo `@post_construct` và periodic task
2. **Fernet encryption** — kiểm tra `cryptography` package đã có trong `requirements.txt` chưa
3. **grpc.aio + SSL** — `grpc.aio.secure_channel()` nhận `grpc.ChannelCredentials` (synchronous object), không cần await
4. **GrpcTrustCertificateClient lazy init** — channel không tạo trong `__init__` vì lúc đó SSL context chưa có; tạo khi gọi lần đầu
5. **Startup ordering** — nếu Xime Framework không hỗ trợ ordering thì cần implement thủ công trong `main.py`
