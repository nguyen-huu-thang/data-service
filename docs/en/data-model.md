# Data Model

**English** | [Tiếng Việt](../vn/data-model.md)

---

## Core Principle

Everything in the platform is a `DataObject`. There are no specialized tables for `image`, `video`, or `document`. Data Service is intentionally unaware of business meaning — it stores objects and tracks their metadata.

```
image         ─┐
video          ├─→  DataObject  (type = IMAGE / VIDEO / DOCUMENT / ...)
document       ├─→
AI artifact    ├─→
dataset        ─┘
```

Application services are responsible for attaching business context. They store only the `object_id` as a reference.

---

## DataObject

The central entity of the entire system.

| Field | Type | Description |
|---|---|---|
| `id` | binary(24) | Object identifier — 24-byte KSUID |
| `tenant_id` | varchar | Tenant context (`null` = platform default) |
| `owner_identity_id` | binary(24) | **Owning identity — all routing starts here** |
| `shard_id` | varchar | Shard containing this object (e.g. `DATA01`, `VN01`) |
| `object_type` | varchar | `IMAGE`, `VIDEO`, `DOCUMENT`, `ARCHIVE`, `DATASET` |
| `visibility` | varchar | `PRIVATE`, `INTERNAL`, `PUBLIC` |
| `status` | varchar | `ACTIVE`, `ARCHIVED`, `SOFT_DELETED`, `PURGED` |
| `current_version_id` | binary(24) | Reference to the current version |
| `storage_provider` | varchar | `LOCAL_DISK` |
| `storage_pointer` | varchar | Relative path to the blob (e.g. `ab12cd34/avatar.jpg`) |
| `metadata_json` | json | Extended metadata (e.g. `{"width": 1920, "height": 1080}`) |
| `permission_version` | int | ACL version — used for cache invalidation |
| `created_at` | timestamp | |
| `updated_at` | timestamp | |

### Domain Model

```python
@dataclass(frozen=True)
class DataObject:
    object_id: bytes           # 24-byte KSUID
    owner_identity_id: bytes   # owning identity
    tenant_id: str | None
    shard_id: str
    object_type: ObjectType
    visibility: Visibility
    status: ObjectStatus
    current_version_id: bytes | None
    storage_pointer: str
    permission_version: int
    created_at: datetime
    updated_at: datetime

    def archive(self) -> 'DataObject':
        return replace(self, status=ObjectStatus.ARCHIVED, updated_at=_now())

    def soft_delete(self) -> 'DataObject':
        return replace(self, status=ObjectStatus.SOFT_DELETED, updated_at=_now())
```

---

## ObjectVersion

Each time the content of an object changes, a new version is created. Versions are immutable records of past content.

| Field | Type | Description |
|---|---|---|
| `id` | binary(24) | Version identifier |
| `object_id` | binary(24) | Parent object |
| `version_number` | int | Sequential: 1, 2, 3, ... |
| `storage_pointer` | varchar | Blob path for this version |
| `content_hash` | varchar | SHA-256 — for integrity check and future deduplication |
| `content_size` | bigint | File size in bytes |
| `mime_type` | varchar | e.g. `image/jpeg`, `application/pdf` |
| `created_by` | binary(24) | Identity that created this version |
| `created_at` | timestamp | |

---

## ObjectPermission

The Access Control List for an object. Each row grants a role to one identity.

| Field | Type | Description |
|---|---|---|
| `id` | binary(24) | |
| `object_id` | binary(24) | |
| `subject_identity_id` | binary(24) | Identity being granted access |
| `role` | varchar | `OWNER`, `EDITOR`, `CONTRIBUTOR`, `VIEWER` |
| `created_at` | timestamp | |

Example ACL for `photo-001`:

```
identity A  →  OWNER
identity B  →  EDITOR
identity C  →  VIEWER
```

---

## ObjectCapability

Fine-grained capability overrides. Used when a role's default capabilities need adjustment for a specific object.

| Field | Type | Description |
|---|---|---|
| `id` | binary(24) | |
| `permission_id` | binary(24) | Links to `object_permission` |
| `capability` | varchar | `READ`, `WRITE`, `DELETE`, `DOWNLOAD`, `SHARE`, `COMMENT` |

---

## ObjectReference

Tracks which services are using an object. Enables safe deletion — an object can only be purged if no service references it.

| Field | Type | Description |
|---|---|---|
| `id` | binary(24) | |
| `object_id` | binary(24) | |
| `service_id` | varchar | e.g. `post-service`, `product-service` |
| `resource_type` | varchar | e.g. `POST`, `PRODUCT`, `MESSAGE` |
| `resource_id` | varchar | ID of the business entity |
| `created_at` | timestamp | |

---

## ObjectAudit

Audit trail for every read, write, share, and delete operation. Can be stored locally or forwarded to a dedicated audit service.

| Field | Type | Description |
|---|---|---|
| `id` | binary(24) | |
| `object_id` | binary(24) | |
| `actor_identity_id` | binary(24) | Who performed the action |
| `action` | varchar | `READ`, `DOWNLOAD`, `UPDATE`, `DELETE`, `SHARE` |
| `created_at` | timestamp | |

---

## Database Schema Overview

### MVP — 4 Core Tables

These 4 tables are sufficient to build avatar storage, attachment handling, document management, media storage, AI artifact storage, and a permission engine.

```
data_object
object_version
object_permission
object_reference
```

### Extended Tables

```
object_capability   ← granular capability overrides (added when needed)
object_tag          ← search support
object_share        ← public sharing (future: signed URLs)
object_audit        ← audit trail
```

---

## Sharding Model

```
identity_id  →  hash  →  partition  →  data shard
```

Each shard runs its own complete, independent set of tables:

```
DATA_SHARD_01
├── data_object
├── object_version
├── object_permission
├── object_capability
├── object_reference
├── object_tag
└── object_audit

DATA_SHARD_02
└── (same schema, independent data)
```

**Key rules:**
- An object's shard is determined once at creation and never changes
- Routing is always deterministic: `identity_id → shard_id → direct route`
- No cross-shard queries within a single request

---

## Important Indexes

```sql
-- data_object: most queries filter by owner + tenant + status
CREATE INDEX idx_data_object_owner ON data_object (owner_identity_id, tenant_id, status, object_type);

-- object_permission: ACL lookup by subject
CREATE INDEX idx_object_perm_subject ON object_permission (subject_identity_id, object_id);

-- object_version: list versions for an object
CREATE INDEX idx_object_version_parent ON object_version (object_id);

-- object_reference: check references before delete
CREATE INDEX idx_object_ref_object ON object_reference (object_id);
```

---

## ID Design — KSUID

All identifiers are 24-byte KSUIDs (K-Sortable Unique Identifiers):

```
4 bytes timestamp + 20 bytes random  =  24 bytes total
```

Properties:
- **Sortable**: newer objects have lexicographically larger IDs
- **Unique**: 20 bytes of randomness — collision probability is negligible
- **Opaque**: does not encode sensitive information
- **Compact**: 24 bytes vs 36 bytes for UUID string

```python
import os, struct, time

KSUID_EPOCH = 1_400_000_000  # ~ May 2014

def generate_id() -> bytes:
    ts = int(time.time()) - KSUID_EPOCH
    return struct.pack('>I', ts) + os.urandom(20)
```
