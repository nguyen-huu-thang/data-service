# Integration

**English** | [Tiếng Việt](../vn/integration.md)

---

## Overview

Data Service integrates with two other Base Platform services:

| Service | Integration purpose |
|---|---|
| `trust-service` | Obtain JWT public keys for token verification; mTLS certificate for service-to-service authentication |
| `identity-service` | Extract and validate `identity_id` from JWT tokens on every request |

Data Service does **not** call `user-service`, `profile-service`, or any application service. It is intentionally isolated from business domains.

---

## Trust Service

The Trust Service manages two independent systems:

1. **JWT Key System** — provides public keys for verifying JWT access tokens
2. **Service Trust System** — manages mTLS certificates for service-to-service communication

### JWT Public Key Sync

Data Service does not call Trust Service on every request. Instead, it maintains a local cache of public keys that is refreshed periodically:

```
Data Service startup
      ↓
Fetch public keys from Trust Service (GetPublicKeys RPC)
      ↓
Cache keys in memory (VerificationKeyCache)
      ↓
Verify incoming JWT tokens locally — no network call per request
      ↓
Periodic refresh (before key expiry)
```

This design means Trust Service has zero impact on request latency. Even if Trust Service is temporarily unavailable, Data Service continues to handle requests using cached keys.

### mTLS Setup

Internal service-to-service calls (e.g. Data Service calling Trust Service for key refresh) use mutual TLS:

```
Data Service startup
      ↓
Request certificate from Trust Service (RotateCertificate RPC)
      ↓
Store certificate locally
      ↓
Use certificate for all outbound internal calls
      ↓
Refresh certificate before expiry
```

### Integration Code Location

```
app/integration/trust/
├── bootstrap/                              ← reads bootstrap payload at startup
├── certificate/
│   ├── GrpcTrustCertificateClient.py       ← gRPC client to fetch certificates from Trust Service
│   ├── TrustCertificateResolver.py         ← resolves the current active certificate
│   └── TrustCertificateSynchronizer.py     ← syncs and persists new certificates
├── key/
│   ├── TrustKeyClient.py                   ← fetches JWT public keys from Trust Service
│   ├── VerificationKeyCache.py             ← in-memory public key cache
│   ├── TrustKeyCleanup.py                  ← cleans up expired keys
│   └── VerificationKeySynchronizer.py      ← periodic key synchronization
├── publicca/                               ← Root CA certificate management
├── scheduler/                              ← scheduled jobs: cert rotation, key refresh, cleanup
├── ssl/                                    ← SSL context setup for gRPC server
└── startup/                                ← startup orchestration for Trust integration
```

---

## Identity Service

Identity Service issues JWT access tokens to authenticated subjects. Data Service consumes these tokens to identify the requesting identity on every inbound request.

### JWT Token Claims

A JWT issued by Identity Service contains:

```json
{
  "sub": "<identity_id as hex>",
  "iss": "identity-service",
  "aud": ["data-service", "user-service", ...],
  "iat": 1700000000,
  "exp": 1700003600,
  "tid": "<tenant_id>"
}
```

Data Service uses:
- `sub` → `identity_id` (owner/requester)
- `aud` → validates the token is intended for this service
- `exp` → validates token is not expired
- `tid` → tenant context

### JWT Verification Flow

```
Inbound HTTP/gRPC request
      ↓
Extract Bearer token from Authorization header
      ↓
Decode JWT header → extract key ID (kid)
      ↓
Look up public key in VerificationKeyCache
      ↓
Verify signature using RSA/ECDSA public key
      ↓
Validate claims: aud, exp, iss
      ↓
Extract identity_id from 'sub' claim
      ↓
Set identity in SecurityContext (XIME)
      ↓
Proceed to use case with verified identity_id
```

All verification happens locally using cached public keys — no call to Identity Service per request.

### Integration Code Location

```
app/integration/identity/
├── client/
│   └── IdentityJwtVerifier.py     ← verifies JWT, extracts identity_id
├── contract/
│   └── IdentityClaims.py          ← JWT claims dataclass
└── resolver/
    └── IdentityResolver.py        ← resolves identity context from request
```

---

## Security Context in XIME

XIME Framework provides a `SecurityContext` that is populated by the authentication middleware. Use cases read identity information from context without touching HTTP headers directly:

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
        # ... create object with identity_id as owner
```

---

## No Runtime Dependency on Trust or Identity Service

Both integrations are designed so that **request processing never blocks on an external service call**:

- JWT verification uses a local key cache (refreshed in background)
- mTLS certificates are cached locally
- If Trust Service is down, Data Service continues with cached keys until they expire

This follows the Base Platform principle: Trust Service can be unavailable for days without affecting other services' request handling.

---

## Request Authentication Summary

```
Client Request
      │
      ├─ gRPC internal call (from another Base Platform service)
      │       └─ mTLS certificate verification
      │
      └─ REST / gRPC external call (from application service)
              └─ JWT verification (local, using cached public key)
                      └─ extract identity_id → set in SecurityContext
```
