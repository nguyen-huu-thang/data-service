# Luồng xác thực — Service Interaction Flows

> Tài liệu này mô tả cách các service trong Base Platform phối hợp với nhau, tập trung vào những gì Data Service cần biết để tích hợp đúng.

---

## 1. Login Flow (Client → Identity → User → Trust)

```text
Client
  POST /api/v1/auth/login
  { identifier, identifierType, credential, credentialType, userShardId? }
    │
    ▼
Identity Service
  1. Normalize identifier (trim, lowercase, unicode NFKC)
  2. Resolve shard:
       └── userShardId hint có? → dùng trực tiếp
       └── Không → gọi Search Service lookup
  3. gRPC → User Service shard (VD: VN01)
       VerifyCredentialRequest { identifier, credential, shard_id, user_agent }
    │
    ▼
User Service
  4. Lookup user bằng identifier (normalized)
  5. Verify credential (BCrypt match)
  6. Trả VerifyCredentialResponse { success, VerifiedIdentity, failure_reason }
    │
    ▼
Identity Service
  7. Nếu success → resolve current signing key (cache từ Trust Service)
  8. Tạo refresh token (với familyId mới)
  9. Tạo access token cho mỗi verifier service đã đăng ký:
       - access_token_A { aud: ["data-service"] }
       - access_token_B { aud: ["profile-service"] }
       - access_token_C { aud: ["notification-service"] }
  10. Trả LoginResponse về Client
    │
    ▼
Client
  Nhận { accessTokens: [...], refreshToken, userShardId }
  Dùng đúng access token khi gọi đúng service
```

---

## 2. Request Flow vào Data Service

```text
Client
  gRPC/REST → Data Service
  Header: Authorization: Bearer <access_token_for_data_service>
    │
    ▼
Data Service — JWT Verification
  1. Extract JWT từ header
  2. Parse header → lấy kid (key ID)
  3. Lookup kid trong VerificationKeyCache (in-memory)
       └── Cache hit + can_verify(now) → dùng public key
       └── Cache miss → sync từ Trust Service → retry
  4. Verify signature với public key
  5. Validate claims:
       - exp > now (chưa hết hạn)
       - aud chứa "data-service"
       - iss == "identity-service"
       - token_version (nếu cần check force logout)
  6. Extract identity_id từ sub
    │
    ▼
Data Service — Authorization
  7. Load ACL từ DB: ObjectPermission where subject_identity_id = identity_id
  8. Evaluate capability (READ/WRITE/DELETE/SHARE/DOWNLOAD)
  9. ALLOW / DENY
    │
    ▼
Data Service — Execute
  10. Thực hiện usecase
  11. Ghi audit trail
```

---

## 3. JWT Public Key Sync Flow

Data Service KHÔNG gọi Trust Service per-request. Thay vào đó cache public key và sync định kỳ.

```text
Data Service Startup
  → gọi Trust Service gRPC (GetVerificationKeys)
  → nhận danh sách KeyContext { key_id, public_key, algorithm, activate_at, expires_at }
  → load vào VerificationKeyCache

Background (định kỳ ~5 phút hoặc khi key miss)
  → Trust Service: GetVerificationKeys (signer=identity, verifier=data-service)
  → update cache
  → clean expired keys (can_verify(now) == False)

Request flow
  → lookup kid trong cache → verify JWT
  → nếu kid không tồn tại → trigger background sync → retry 1 lần
```

---

## 4. mTLS Setup Flow

Data Service thiết lập mTLS khi bootstrap, không phải per-request.

```text
Data Service Startup
  → gọi Trust Service (gửi cert_refresh_token từ config / bootstrap token)
  → Trust verify token: is_deleted=FALSE, expires_at > now
  → Trust issue certificate mới (private_key_encrypted, public_cert)
  → Data Service decrypt private key, load vào TLS context
  → Sử dụng cert này cho TẤT CẢ outbound gRPC calls đến các service khác

Cert Rotation (định kỳ trước khi cert hết hạn)
  → Dùng cert_refresh_token mới nhận được từ lần issue trước
  → Gọi Trust Service rotate
  → Nhận cert mới + refresh token mới
```

---

## 5. Shard Resolution cho Data Service

Khi client (application service) muốn upload/download object:

```text
Application Service
  → Biết identity_id của user (từ JWT của user gửi lên)
  → Tính shard: hash(identity_id) → DATA_SHARD_XX
  → Lookup shard host từ Trust Service (hoặc local cache)
  → Gọi thẳng Data Service shard tương ứng

Data Service shard
  → Verify JWT
  → Verify shard_id trong request khớp với shard của mình
  → Thực hiện operation
```

Nguyên tắc: **deterministic routing, không broadcast toàn cluster**.

---

## 6. Token Hierarchy

```text
Trust Service
  ├── generate key pair (RSA/EC/EdDSA)
  ├── private_key_encrypted → Identity Service
  └── public_key → tất cả verifier services (incl. Data Service)

Identity Service
  ├── dùng private_key ký JWT
  └── JWT { sub=identity_id, aud=[data-service, ...], token_version }

Client
  └── gửi JWT khi gọi Data Service

Data Service
  └── verify JWT bằng public_key từ Trust Service
```

---

## Các điểm Data Service phải implement

| Việc cần làm | Mô tả |
| --- | --- |
| JWT verification | Verify signature, check aud, exp, iss |
| VerificationKeyCache | In-memory cache public keys, sync định kỳ từ Trust |
| mTLS client | Load cert từ Trust Service, dùng cho outbound calls |
| Shard ID validation | Verify request đến đúng shard (chống mis-routing) |
| Audit trail | Ghi lại mọi access (ai, làm gì, lúc nào) |
| Service registration | Đăng ký với Trust Service là verifier của Identity Service |
