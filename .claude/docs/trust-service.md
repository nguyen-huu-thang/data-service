# Trust Service — Tài liệu thiết kế

> Tài liệu này cung cấp context về Trust Service cho Data Service dev — Data Service cần public key từ Trust Service để verify JWT.

## Vai trò

Trust Service là **trust infrastructure của toàn platform** — internal CA của toàn hệ thống.

Chịu trách nhiệm:

- Certificate authority (CA)
- Generate và rotate asymmetric key pair
- Cấp certificate cho service (mTLS)
- Quản lý trust chain giữa các service
- **Quản lý Shard Registry** — danh sách service + shard toàn cluster

> Lưu ý: Tên cũ là "Key Service" — trong code cũ có thể vẫn còn tên này.

---

## Hai hệ thống độc lập

### A. JWT Key System (dùng cho authentication user)

- Identity Service dùng private key để ký JWT
- Các service khác (gồm Data Service) verify JWT bằng public key
- Time-based rotation — không cần gọi Trust Service runtime
- Backward-compatible: rotate ≠ expiration, verify luôn hợp lệ với key cũ

**Time Model:**

```text
activate_at  → bắt đầu SIGN (Identity Service switch sang key mới)
expires_at   → kết thúc VERIFY (các service không còn accept key này)
```

**Key Business Logic:**

```python
def can_sign(self, now: datetime) -> bool:
    return not self.is_deleted and now >= self.activate_at

def can_verify(self, now: datetime) -> bool:
    return not self.is_deleted and now < self.expires_at
```

Key rotation không invalidate ngay — window `activate_at → expires_at` cho phép cả signing và verifying tồn tại song song.

### B. Service Trust System (dùng cho service-to-service)

- Certificate-based identity (mTLS)
- Rotation chủ động (request-based) với refresh token

---

## Database Schema

### services

```sql
id          VARCHAR(20) PK    (service ID ngắn, VD: "identity", "data", "user")
name        VARCHAR(100)
tenant      VARCHAR(100)
status      VARCHAR(20)       ACTIVE / INACTIVE
created_at  TIMESTAMP
```

### shards

```sql
id          VARCHAR(10) PK    (VD: VN01, EU02, DATA_SHARD_07)
service_id  VARCHAR(20) FK → services
host        VARCHAR(100)
port        INT
status      VARCHAR(20)       ACTIVE / INACTIVE / MAINTENANCE / DEAD
created_at  TIMESTAMP

Index: idx_shards_service(service_id), idx_shards_status(status)
```

### key_policies

```sql
id                       BYTEA PK (KSUID 20 bytes)
signer_service_id        VARCHAR(20) FK → services
verifier_service_id      VARCHAR(20) FK → services
algorithm                VARCHAR(20)    RSA / ECDSA
key_size                 INT            2048/3072/4096/256/384
key_lifetime_seconds     BIGINT
rotation_interval_seconds BIGINT
preload_seconds          BIGINT
created_at, updated_at   TIMESTAMP

Constraint: UNIQUE(signer_service_id, verifier_service_id)
            signer_service_id != verifier_service_id
```

### keys

```sql
id                    BYTEA PK (KSUID 20 bytes)
signer_service_id     VARCHAR(20) FK → services
verifier_service_id   VARCHAR(20) FK → services
public_key            TEXT
private_key_encrypted TEXT           (AES-GCM encrypted)
algorithm             VARCHAR(20)
key_size              INT
created_at            TIMESTAMP
activate_at           TIMESTAMP      bắt đầu được dùng để SIGN
expires_at            TIMESTAMP      hết hạn VERIFY
is_deleted            BOOLEAN

Constraint: UNIQUE(signer_service_id, verifier_service_id, activate_at)
            expires_at > activate_at

Index: idx_keys_signer_active(signer_service_id, is_deleted, expires_at)
       idx_keys_pair_active(signer_service_id, verifier_service_id, expires_at)
```

### certificates

```sql
id                    BYTEA PK (KSUID 20 bytes)
service_id            VARCHAR(20) FK → services
public_cert           TEXT
private_key_encrypted TEXT
issued_at             TIMESTAMP
expires_at            TIMESTAMP
status                VARCHAR(20)
is_deleted            BOOLEAN

Constraint: UNIQUE(service_id, issued_at)
            expires_at > issued_at

Index: idx_cert_service_expire(service_id, expires_at)
```

### cert_refresh_tokens

```sql
id           BYTEA PK (KSUID 20 bytes)
token_hash   TEXT UNIQUE
is_bootstrap BOOLEAN
issued_at    TIMESTAMP
expires_at   TIMESTAMP
is_deleted   BOOLEAN
```

### Audit Tables

```text
key_access_logs:   theo dõi ai đọc key nào (khi nào, IP, success)
key_events:        lifecycle events của key (CREATED, ROTATED, DELETED)
cert_events:       lifecycle events của cert
```

---

## Private Key Encryption

Trust Service encrypt private key bằng AES-256-GCM trước khi lưu DB:

```python
ALGORITHM = "AES/GCM/NoPadding"
IV_LENGTH = 12 bytes
TAG_LENGTH = 128 bits

encrypt(plaintext):
    iv = random 12 bytes
    ciphertext = AES_GCM(key, iv, plaintext)
    return base64(iv + ciphertext)

decrypt(encrypted):
    decoded = base64_decode(encrypted)
    iv = decoded[:12]
    ciphertext = decoded[12:]
    return AES_GCM_decrypt(key, iv, ciphertext)
```

---

## Cert Rotation Flow

```text
Service → Trust Service (qua mTLS)
  → gửi cert_refresh_token
  → Trust verify: token tồn tại, is_deleted = FALSE, expires_at > now
  → issue cert mới
  → mark old refresh token is_deleted = TRUE (one-time use)
  → trả cert mới + refresh token mới
```

---

## Security Model

| Thành phần | Nguyên tắc |
| --- | --- |
| Private key JWT | AES-GCM encrypted, chỉ Identity Service decrypt |
| mTLS | Certificate-based, không dùng API key |
| Cert Refresh Token | One-time use, không reuse |
| Key Audit | Mọi lần đọc key đều log (key_access_logs) |

---

## Caching và Synchronization

- **JWT Public Keys**: Service cache trong memory (ConcurrentHashMap). Không gọi Trust Service per-request.
- **Background Sync**: Định kỳ hoặc khi key miss → sync từ Trust Service → update cache → clean expired.
- **Cert**: Chỉ gọi Trust Service khi bootstrap hoặc rotate cert — không tham gia request flow.

### Pattern cache public key (VerificationKeyResolver)

```python
class VerificationKeyCache:
    def __init__(self):
        self._cache: dict[str, KeyContext] = {}

    def resolve(self, key_id: str) -> KeyContext | None:
        key = self._cache.get(key_id)
        if key and key.can_verify(datetime.now(timezone.utc)):
            return key
        return None

    def update(self, keys: list[KeyContext]) -> None:
        for key in keys:
            self._cache[key.key_id] = key

    def clean_expired(self) -> None:
        now = datetime.now(timezone.utc)
        self._cache = {k: v for k, v in self._cache.items() if v.can_verify(now)}
```

---

## Nguyên tắc thiết kế

1. Tách biệt JWT Key System và mTLS Cert System
2. Key rotation ≠ Cert rotation
3. Không revoke JWT ngay lập tức (TTL-based expiry)
4. Trust Service là control-plane, không phải data-plane
5. Mọi private key phải encrypt trước khi lưu DB

---

## Ý nghĩa với Data Service

- Data Service lấy public key từ Trust Service để **verify JWT** (cache, không gọi runtime per-request)
- Data Service nhận cert từ Trust Service để **thiết lập mTLS** với các service khác
- Data Service phải **đăng ký trong Trust Service** là verifier của Identity Service (để nhận access token có `aud: "data-service"`)
- Trust Service là nguồn duy nhất của cryptographic trust trong toàn hệ thống
- Shard của Data Service được đăng ký trong Trust Service `shards` table
