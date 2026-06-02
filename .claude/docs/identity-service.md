# Identity Service — Tài liệu thiết kế

> Tài liệu này cung cấp context về Identity Service cho Data Service dev — Data Service cần verify JWT từ Identity Service và tích hợp `identity_id` làm owner.

## Vai trò

Identity Service là **"authentication infrastructure của toàn platform"**.

Chịu trách nhiệm: authentication orchestration, JWT issuing, refresh token handling, token revocation, identity verification, platform-level authorization.

**Không phải**: user database, profile service, business account service, centralized credential database.

Hỗ trợ: human identity, bot identity, service identity, machine identity, AI agent identity.

---

## Identity Model

Identity = **"authenticated subject abstraction"** — không đồng nghĩa với user/profile/account.

Identity chỉ chứa:

- `identity_id` (KSUID 24 bytes)
- Authentication metadata
- Token metadata
- Platform authorization metadata

Thông tin domain thực tế **không** nằm trong identity-service:
```
human identity_id → user-service → user profile
bot identity_id   → bot-service  → bot metadata
```

---

## Credential Ownership

Credential **không** lưu trong identity-service. Credential nằm ở service sở hữu domain:

```
Human credential   → user-service   (password, oauth, passkey, MFA)
Bot credential     → bot-service
System credential  → system-service
```

---

## Login Flow (Chi tiết)

```
Client → Identity Service (POST /api/v1/auth/login)
  1. Validate request (identifier, credential, credentialType)
  2. Normalize identifier (uppercase → lowercase, trim, unicode NFKC)
  3. Resolve shard:
       - Nếu client gửi userShardId hint → dùng trực tiếp (bypass search)
       - Nếu không → gọi Search Service để lookup shard
  4. Gọi User Service qua gRPC (VerifyCredentialRequest)
       - identifier, identifierType, credential (raw — không log!)
       - user_agent, shard_id
  5. User Service trả về VerifyCredentialResponse:
       - success: bool
       - identity (VerifiedIdentity)
       - failure_reason: INVALID_CREDENTIAL / ACCOUNT_LOCKED / ...
  6. Nếu success → tạo refresh token + access tokens
  7. Lấy current signing key từ Trust Service (cache, không gọi runtime)
  8. Tạo access token cho từng verifier service đã đăng ký
  9. Trả LoginResponse về client
```

### VerifiedIdentity (từ User Service)

```
identity_id   (Id 24 bytes)
subjectType   (human, bot, service, ai_agent)
shardId       (VD: VN01, EU02)
serviceId     (service gốc của subject)
tenantId
```

---

## JWT Access Token

### Claims (thực tế từ code NimbusJwtTokenGenerator)

```json
{
  "jti": "...",
  "sub": "<identity_id as hex string>",
  "iss": "identity-service",
  "aud": ["data-service", "profile-service", "..."],
  "iat": 1700000000,
  "exp": 1700000900,
  "nbf": 1700000000,
  "auth_time": 1700000000,
  "token_version": 1
}
```

**Quan trọng:**

- `aud` là **danh sách** verifier service ID đã đăng ký với Trust Service
- **Không có `roles` hay `permissions`** trong access token — đó là application-level authorization
- `token_version` tăng khi force logout / lock account → toàn bộ token cũ invalid
- `jti` là unique token ID — dùng để revoke refresh token (lưu blacklist)

### Multi-Audience Access Token

Identity Service tạo **nhiều access token**, mỗi token cho một verifier service:

```
signing key K → access_token_A (aud: ["data-service"])
signing key K → access_token_B (aud: ["profile-service"])
signing key K → access_token_C (aud: ["notification-service"])
```

Client nhận tất cả trong LoginResponse và dùng đúng token cho đúng service.

**Với Data Service**: Data Service phải được đăng ký là verifier trong Trust Service. Khi nhận request, Data Service verify rằng `aud` trong token chứa `"data-service"`.

---

## Refresh Token

```
jti           (unique token ID)
familyId      (theo dõi chuỗi rotation)
parentTokenId (token cha trong chuỗi)
identity_id
issued_at / expires_at (30 ngày)
token_version
```

**Family tracking**: phát hiện token reuse — nếu cùng family được dùng lại → toàn bộ family invalid (rotation attack detection).

---

## Token Architecture

### Access Token

- Stateless JWT, asymmetric signed (RS256 / ES256 / EdDSA), short-lived (~15 phút)
- Verify locally bằng public key từ Trust Service — **không gọi Identity Service runtime**
- Không realtime revoke — TTL ngắn, tự hết hạn

### Refresh Token — Lifecycle

- Signed JWT, revocable, dùng để issue access token mới
- Revoke bằng distributed blacklist (`jti` hoặc `hash(token)`)
- **Rotation**: dùng refresh_token_A → issue refresh_token_B → A invalid

---

## Identifier Normalization

User Service normalize identifier trước khi hash/lookup:

```python
# EMAIL, USERNAME
value = value.strip().lower()
value = unicodedata.normalize('NFKC', value)

# PHONE
value = value.strip()
value = ''.join(c for c in value if c.isdigit())
value = unicodedata.normalize('NFKC', value)
```

Nguyên tắc: **deterministic** — normalize(normalize(x)) == normalize(x).

---

## Authorization Model

| Tầng | Quản lý ở đâu | Ví dụ |
| --- | --- | --- |
| Platform Authorization | identity-service | platform_admin, support, developer |
| Application Authorization | application services | post_owner, moderator, customer |

Data Service xử lý **Application Authorization** riêng — capability-based ACL trên DataObject.

---

## Service-to-Service Security

Giao tiếp nội bộ dùng **mTLS** + certificate-based authentication (cấp bởi Trust Service).

Certificate chứa: `service_id`, `shard_id`.

Request payload cũng chứa `service_id`, `shard_id` — compare với mTLS identity để chống spoofing.

---

## Ý nghĩa với Data Service

- Data Service nhận JWT từ client → verify signature bằng public key từ Trust Service → extract `identity_id`
- `identity_id` trong JWT là nguồn duy nhất để xác định owner — Data Service **không** gọi user-service
- Data Service phải check `aud` chứa `"data-service"` trước khi accept token
- Data Service phải check `token_version` nếu lưu user state (phòng force logout)
- Giao tiếp nội bộ với Identity/User Service (nếu cần) qua mTLS
