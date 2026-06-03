# Authorization

**English** | [Tiếng Việt](../vn/authorization.md)

---

## Model

Data Service uses **Capability-Based Access Control (CBAC)**. Access to an object is determined by evaluating the requesting identity's capabilities against the object's ACL.

---

## Capabilities

A capability represents a specific action that can be performed on an object:

| Capability | Description |
|---|---|
| `READ` | View object metadata |
| `WRITE` | Upload a new version / update metadata |
| `DELETE` | Soft-delete the object |
| `DOWNLOAD` | Retrieve the binary content (blob) |
| `SHARE` | Grant or revoke access for other identities |
| `COMMENT` | Add comments (future) |

---

## Roles

A role is a predefined set of capabilities. Assigning a role to an identity is the primary way to grant access.

| Role | Capabilities |
|---|---|
| `OWNER` | READ, WRITE, DELETE, DOWNLOAD, SHARE |
| `EDITOR` | READ, WRITE, DOWNLOAD |
| `CONTRIBUTOR` | READ, WRITE |
| `VIEWER` | READ, DOWNLOAD |

The owner role is automatically assigned to the `owner_identity_id` at object creation time.

Additional fine-grained capabilities can be assigned per identity using the `object_capability` table when the default role mapping is insufficient.

---

## ACL Structure

Each object has an Access Control List stored in `object_permission`:

```
object photo-001:
  identity-A  →  OWNER       (READ, WRITE, DELETE, DOWNLOAD, SHARE)
  identity-B  →  EDITOR      (READ, WRITE, DOWNLOAD)
  identity-C  →  VIEWER      (READ, DOWNLOAD)
```

---

## Visibility

The `visibility` field on a `DataObject` provides a shortcut for coarse-grained access control:

| Visibility | Access behavior |
|---|---|
| `PRIVATE` | Only identities explicitly in the ACL |
| `INTERNAL` | Subject to policy (e.g. all identities within the same tenant) |
| `PUBLIC` | No authorization required for READ/DOWNLOAD |

Visibility checks happen before ACL evaluation. A `PUBLIC` object bypasses the ACL for read/download.

---

## Authorization Flow

```
Incoming request
      ↓
Extract JWT from header
      ↓
Verify JWT signature    ← uses public key from Trust Service cache
      ↓
Extract identity_id from JWT claims
      ↓
Resolve object shard    ← from object_id or owner_identity_id
      ↓
Check object visibility
      ↓ (if not PUBLIC)
Load ACL from object_permission table
      ↓
Evaluate: does identity have the required capability?
      ↓
ALLOW  /  DENY
```

All steps happen within the Data Service — no external authorization service is called at request time.

---

## Implementation

Authorization logic lives in `application/service/authorization/`:

```python
class AuthorizationService:
    def __init__(
        self,
        load_permission_port: LoadPermissionPort,
    ) -> None:
        self._load_permission = load_permission_port

    async def check(
        self,
        identity_id: bytes,
        object_id: bytes,
        required: Capability,
    ) -> bool:
        permissions = await self._load_permission.find_by_object(object_id)
        for perm in permissions:
            if perm.subject_identity_id == identity_id:
                return required in perm.role.capabilities()
        return False
```

Use cases call `AuthorizationService` before performing any state-changing operation:

```python
class DeleteObjectUseCase:
    async def execute(self, command: DeleteObjectCommand) -> None:
        allowed = await self._auth.check(
            command.requester_identity_id,
            command.object_id,
            Capability.DELETE,
        )
        if not allowed:
            raise PermissionDeniedError(command.object_id)
        # ... proceed with deletion
```

---

## Sharing

Sharing is the act of granting or revoking access to an object for another identity. Only an identity with the `SHARE` capability (i.e. `OWNER` role) can perform this operation.

```
identity-A (OWNER) calls: grant_permission(object_id, identity-D, role=VIEWER)
      ↓
AuthorizationService.check(identity-A, object_id, SHARE)  → ALLOW
      ↓
GrantPermissionUseCase: insert into object_permission
```

---

## Permission Versioning

The `permission_version` field on `DataObject` is incremented whenever the ACL changes. This is used by downstream caches to invalidate stale permission data without a full cache flush.

---

## What Data Service Does NOT Do

- Does not perform platform-level authorization (admin, platform role) — that is Identity Service's concern
- Does not call an external authorization service on each request — ACL is evaluated locally
- Does not implement attribute-based policies (ABAC) — only capability-based roles
