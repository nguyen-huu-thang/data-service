# Kế hoạch sửa code — Đồng bộ với thiết kế mới

> Tài liệu này liệt kê tất cả những gì cần sửa sau khi cập nhật database schema và domain model.
> Thực hiện theo đúng thứ tự phase để tránh lỗi compile/runtime.

---

## Tổng quan vấn đề phát hiện

Sau khi đọc code hiện tại, có **6 nhóm vấn đề** cần giải quyết:

| Nhóm | Vấn đề | Mức độ |
|------|---------|--------|
| A | Domain Model thiếu methods | Nghiêm trọng |
| B | Constructor mismatch — use case ↔ domain | Nghiêm trọng |
| C | Audit thiếu actor context | Quan trọng |
| D | Authorization thiếu System Permission layer | Quan trọng |
| E | Import paths dùng legacy `app.common.constants` | Vừa |
| F | Dependency bindings thiếu — sẽ crash startup | Nghiêm trọng |

---

## Phase 1 — Sửa Domain Model

### 1.1 `DataObject` — thêm missing methods

**File:** `app/domain/object/model/DataObject.py`

**Vấn đề:**

- `AuthorizationService` gọi `obj.is_public()` → method không tồn tại
- `RestoreObjectUseCase` gọi `obj.can_transition_to(status)` → không tồn tại
- `RestoreObjectUseCase` gọi `restored = obj.restore(now)` → method hiện tại trả `None`, không có param `now`
- `CreateVersionUseCase` gọi `updated_obj = obj.update_version(version_id, now)` → không tồn tại (chỉ có `update_current_version(version_id)` trả `None`)

**Sửa:**

Thêm 4 methods sau vào `DataObject`:

```python
def is_public(self) -> bool:
    return self._visibility == ObjectVisibility.PUBLIC

def can_transition_to(self, target: ObjectStatus) -> bool:
    allowed = {
        ObjectStatus.ACTIVE:       {ObjectStatus.ARCHIVED, ObjectStatus.SOFT_DELETED},
        ObjectStatus.ARCHIVED:     {ObjectStatus.ACTIVE, ObjectStatus.SOFT_DELETED},
        ObjectStatus.SOFT_DELETED: {ObjectStatus.ACTIVE, ObjectStatus.PURGED},
        ObjectStatus.PURGED:       set(),
    }
    return target in allowed.get(self._status, set())

def restore(self, now: datetime) -> 'DataObject':
    # Trả về instance mới (immutable pattern)
    new = DataObject(...)  # copy all fields, override status + updated_at
    return new

def update_version(self, version_id: bytes, now: datetime) -> 'DataObject':
    # Trả về instance mới với current_version_id mới
    new = DataObject(...)
    return new
```

**Lưu ý:** Cần thêm `updated_at: datetime` vào constructor của `DataObject` để các methods trên có thể track thời gian. Hiện tại constructor không có `updated_at`.

**Cụ thể cần làm:**
1. Thêm `updated_at: datetime` vào constructor (và `created_at: datetime`)
2. Thêm property `updated_at`, `created_at`
3. Sửa các mutating methods (`archive`, `soft_delete`, `restore`, `update_current_version`) để trả về `DataObject` mới thay vì mutate in-place
4. Thêm `is_public()`, `can_transition_to()`, `update_version()` như trên

---

### 1.2 `ObjectPermission` — kiểm tra `has_capability()`

**File:** `app/domain/permission/model/ObjectPermission.py`

**Vấn đề:** `AuthorizationService` gọi `permission.has_capability(capability)` nhưng chưa chắc method này tồn tại.

**Sửa:** Thêm method nếu chưa có:

```python
def has_capability(self, capability: Capability) -> bool:
    from app.common.constants.Capability import Capability as Cap
    role_caps = {
        Role.OWNER:  {Cap.READ, Cap.WRITE, Cap.DELETE, Cap.SHARE, Cap.DOWNLOAD},
        Role.EDITOR: {Cap.READ, Cap.WRITE, Cap.DOWNLOAD},
        Role.VIEWER: {Cap.READ, Cap.DOWNLOAD},
    }
    return capability in role_caps.get(self._role, set())
```

---

## Phase 2 — Fix Import Paths

**Vấn đề:** Một số use case và port file import từ `app.common.constants.*` (legacy) trong khi domain model đã chuyển sang `domain.*.valueobject.*`.

**Files cần sửa:**

### 2.1 `CreateObjectUseCase.py`
```python
# XÓA (cũ):
from app.common.constants.ObjectStatus import ObjectStatus
from app.common.constants.Role import Role

# THAY BẰNG:
from domain.object.valueobject.ObjectStatus import ObjectStatus
from domain.permission.role.Role import Role
```

### 2.2 `RestoreObjectUseCase.py`
```python
# XÓA:
from app.common.constants.ObjectStatus import ObjectStatus

# THAY BẰNG:
from domain.object.valueobject.ObjectStatus import ObjectStatus
```

Rà soát tương tự tất cả use case còn lại (`ArchiveObjectUseCase`, `DeleteObjectUseCase`, `PurgeObjectUseCase`, `GetObjectUseCase`, `CreateVersionUseCase`, ...).

### 2.3 `LoadPermissionPort.py`
```python
# XÓA (sai path):
from app.domain.permission.ObjectPermission import ObjectPermission

# THAY BẰNG:
from app.domain.permission.model.ObjectPermission import ObjectPermission
```

---

## Phase 3 — Audit: thêm actor context

### 3.1 `SaveAuditPort.py`

**File:** `app/application/port/outbound/audit/SaveAuditPort.py`

**Sửa signature:**

```python
class SaveAuditPort(Protocol):
    async def record(
        self,
        object_id: bytes,
        actor_identity_id: bytes,
        actor_subject_type: str,
        actor_name: str,
        action: str,
    ) -> None: ...
```

### 3.2 `AuditService.py`

**File:** `app/application/service/audit/AuditService.py`

**Sửa signature:**

```python
async def record(
    self,
    object_id: bytes,
    actor_identity_id: bytes,
    actor_subject_type: str,
    actor_name: str,
    action: str,
) -> None:
    try:
        await self._save.record(
            object_id, actor_identity_id, actor_subject_type, actor_name, action
        )
    except Exception:
        _log.warning(...)
```

### 3.3 Infrastructure — `SqlAlchemyObjectAuditRepository`

**File:** `app/infrastructure/persistence/repository/SqlAlchemyObjectAuditRepository.py`

Cập nhật method `record()` để truyền `actor_subject_type` và `actor_name` vào entity khi tạo `ObjectAudit`.

---

## Phase 4 — Commands/Queries: thêm subject context

Tất cả commands/queries cần thêm 2 fields để use case có thể:
- Truyền vào `AuthorizationService` (subject_type cho system permission check)
- Truyền vào `AuditService` (để ghi actor info đầy đủ)

### 4.1 Object commands/queries

**Files cần sửa:**

| File | Thêm fields |
|------|-------------|
| `dto/object/CreateObjectCommand.py` | `requester_subject_type: str`, `requester_name: str` |
| `dto/object/GetObjectQuery.py` | `requester_subject_type: str`, `requester_name: str` |
| `dto/object/DeleteObjectCommand.py` | `requester_subject_type: str`, `requester_name: str` |
| `dto/object/DownloadObjectQuery.py` | `requester_subject_type: str`, `requester_name: str` |
| `dto/object/ArchiveObjectCommand.py` | `requester_subject_type: str`, `requester_name: str` |
| `dto/object/RestoreObjectCommand.py` | `requester_subject_type: str`, `requester_name: str` |
| `dto/object/PurgeObjectCommand.py` | `requester_subject_type: str`, `requester_name: str` |

### 4.2 Version commands/queries

| File | Thêm fields |
|------|-------------|
| `dto/version/CreateVersionCommand.py` | `requester_subject_type: str`, `requester_name: str` |
| `dto/version/GetVersionQuery.py` | `requester_subject_type: str`, `requester_name: str` |
| `dto/version/ListVersionsQuery.py` | `requester_subject_type: str`, `requester_name: str` |
| `dto/version/DownloadVersionQuery.py` | `requester_subject_type: str`, `requester_name: str` |

---

## Phase 5 — Sửa Constructor Calls trong Use Cases

### 5.1 `CreateObjectUseCase.py` — nhiều lỗi nhất

**Lỗi 1:** Tạo `DataObject` thiếu `owner_subject_type`, dùng `metadata_json` thay vì `metadata`:

```python
# HIỆN TẠI (sai):
obj = DataObject(
    object_id=object_id,
    owner_identity_id=command.requester_identity_id,
    # THIẾU: owner_subject_type
    metadata_json={},           # sai tên param
    created_at=now, updated_at=now,  # không có trong constructor hiện tại
    ...
)

# SAU KHI SỬA:
obj = DataObject(
    object_id=object_id,
    owner_identity_id=command.requester_identity_id,
    owner_subject_type=command.requester_subject_type,  # THÊM
    metadata={},                # đúng tên param
    created_at=now,
    updated_at=now,
    ...
)
```

**Lỗi 2:** Tạo `ObjectVersion` sai tên param và thiếu fields:

```python
# HIỆN TẠI (sai):
version = ObjectVersion(
    content_hash=content_hash,          # str, cần ContentHash object
    mime_type=command.content_type,      # str, cần MimeType object
    created_by=command.requester_identity_id,  # sai tên! → created_by_identity_id
    # THIẾU: created_by_subject_type
    ...
)

# SAU KHI SỬA:
from domain.object.valueobject.ContentHash import ContentHash
from domain.object.valueobject.MimeType import MimeType

version = ObjectVersion(
    content_hash=ContentHash(content_hash),
    mime_type=MimeType(command.content_type),
    created_by_identity_id=command.requester_identity_id,
    created_by_subject_type=command.requester_subject_type,  # THÊM
    ...
)
```

**Lỗi 3:** Tạo `ObjectPermission` thiếu `subject_type`:

```python
# HIỆN TẠI (sai):
permission = ObjectPermission(
    permission_id=permission_id,
    object_id=object_id,
    subject_identity_id=command.requester_identity_id,
    role=Role.OWNER,
    created_at=now,
)

# SAU KHI SỬA:
permission = ObjectPermission(
    permission_id=permission_id,
    object_id=object_id,
    subject_identity_id=command.requester_identity_id,
    subject_type=command.requester_subject_type,  # THÊM
    role=Role.OWNER,
    created_at=now,
)
```

**Lỗi 4:** Thiếu `audit.record()` sau khi tạo thành công:

```python
# Thêm sau return result (ngoài try block):
await self._audit.record(
    object_id=object_id,
    actor_identity_id=command.requester_identity_id,
    actor_subject_type=command.requester_subject_type,
    actor_name=command.requester_name,
    action="CREATE",
)
```

### 5.2 `CreateVersionUseCase.py`

Tương tự lỗi 2 của 5.1 (ObjectVersion sai tên param, thiếu subject_type).

Thêm: `obj.update_version(version_id, now)` — sau Phase 1 sẽ trả `DataObject` mới, cần dùng đúng:
```python
updated_obj = obj.update_version(version_id, now)
await self._save.update(updated_obj)
```

### 5.3 `RestoreObjectUseCase.py`

```python
# HIỆN TẠI (sai):
restored = obj.restore(now)   # trả None hiện tại
await self._save.update(restored)  # save(None) → crash

# Sau Phase 1, restore() trả DataObject mới → code này sẽ đúng.
# Không cần sửa thêm sau khi fix domain model.
```

Cập nhật audit call:
```python
await self._audit.record(
    obj.object_id, command.requester_identity_id,
    command.requester_subject_type, command.requester_name,
    "RESTORE"
)
```

### 5.4 Các use cases còn lại

Rà soát tất cả `audit.record()` calls và thêm `requester_subject_type`, `requester_name`:

| Use Case | Audit action |
|----------|-------------|
| `GetObjectUseCase` | "READ" |
| `DeleteObjectUseCase` | "DELETE" |
| `DownloadObjectUseCase` | "DOWNLOAD" |
| `ArchiveObjectUseCase` | "ARCHIVE" |
| `RestoreObjectUseCase` | "RESTORE" |
| `PurgeObjectUseCase` | "PURGE" |
| `CreateVersionUseCase` | "CREATE_VERSION" |
| `DownloadVersionUseCase` | "DOWNLOAD" |

---

## Phase 6 — Authorization: thêm System Permission layer

### 6.1 Tạo port mới: `LoadSubjectPermissionPort`

**File mới:** `app/application/port/outbound/permission/LoadSubjectPermissionPort.py`

```python
from typing import Protocol
from app.domain.permission.model.SubjectPermission import SubjectPermission

class LoadSubjectPermissionPort(Protocol):
    async def find_by_subject(
        self, subject_identity_id: bytes
    ) -> list[SubjectPermission]: ...

    async def has_permission(
        self, subject_identity_id: bytes, permission: str
    ) -> bool: ...
```

### 6.2 Sửa `AuthorizationService`

**File:** `app/application/service/authorization/AuthorizationService.py`

**Thêm dependency** vào constructor:
```python
def __init__(
    self,
    load_permission_port: LoadPermissionPort,
    load_subject_permission: LoadSubjectPermissionPort,  # THÊM
) -> None:
```

**Sửa `require_capability()` signature** để nhận `requester_subject_type`:
```python
async def require_capability(
    self,
    requester_identity_id: bytes,
    requester_subject_type: str,   # THÊM
    obj: DataObject,
    capability: Capability,
) -> None:
```

**Thêm System Permission check** ở đầu method:
```python
async def require_capability(self, requester_identity_id, requester_subject_type, obj, capability):
    # 1. PUBLIC object — READ/DOWNLOAD bypass toàn bộ ACL
    if obj.is_public() and capability in _PUBLIC_FREE_CAPS:
        return

    # 2. System Permission — override mọi ACL (DATA_READ_ANY, DATA_DELETE_ANY, ...)
    system_cap = _CAPABILITY_TO_SYSTEM_PERMISSION.get(capability)
    if system_cap:
        has_sys = await self._load_subject_permission.has_permission(
            requester_identity_id, system_cap
        )
        if has_sys:
            return

    # 3. Owner có toàn quyền
    if obj.owner_identity_id == requester_identity_id:
        return

    # 4. Kiểm tra ACL (Object Permission)
    permission = await self._load_permission.find_by_subject_and_object(
        subject_identity_id=requester_identity_id,
        object_id=obj.object_id,
    )
    if permission is None or not permission.has_capability(capability):
        raise PermissionDeniedException()
```

**Thêm mapping constant:**
```python
from app.domain.permission.capability.ObjectCapability import ObjectCapability

_CAPABILITY_TO_SYSTEM_PERMISSION = {
    Capability.READ:     ObjectCapability.DATA_READ_ANY,
    Capability.WRITE:    ObjectCapability.DATA_WRITE_ANY,
    Capability.DELETE:   ObjectCapability.DATA_DELETE_ANY,
    Capability.SHARE:    ObjectCapability.DATA_SHARE_ANY,
    Capability.DOWNLOAD: ObjectCapability.DATA_READ_ANY,
}
```

### 6.3 Cập nhật tất cả use cases gọi `require_capability()`

Thêm `requester_subject_type` vào mỗi call:

```python
# TRƯỚC:
await self._auth.require_capability(
    query.requester_identity_id, obj, Capability.READ
)

# SAU:
await self._auth.require_capability(
    query.requester_identity_id,
    query.requester_subject_type,   # THÊM
    obj,
    Capability.READ,
)
```

Files cần cập nhật: `GetObjectUseCase`, `DownloadObjectUseCase`, `ArchiveObjectUseCase`, `DeleteObjectUseCase`, `CreateVersionUseCase`, `GetVersionUseCase`, `ListVersionsUseCase`, `DownloadVersionUseCase`.

---

## Phase 7 — Dependency bindings

### 7.1 Thêm bindings còn thiếu vào `dependency.py`

**File:** `app/config/dependency.py`

Hiện tại chỉ bind generic repos. Use cases inject các specific ports nhưng không có binding.

**Thêm imports:**
```python
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.application.port.outbound.version.LoadVersionPort import LoadVersionPort
from app.application.port.outbound.version.SaveVersionPort import SaveVersionPort
from app.application.port.outbound.permission.LoadPermissionPort import LoadPermissionPort
from app.application.port.outbound.permission.SavePermissionPort import SavePermissionPort
from app.application.port.outbound.permission.LoadSubjectPermissionPort import LoadSubjectPermissionPort
from app.application.port.outbound.audit.SaveAuditPort import SaveAuditPort
```

**Thêm vào `dependency.bind({})`:**
```python
# Object specific ports
LoadObjectPort:  SqlAlchemyObjectRepository,
SaveObjectPort:  SqlAlchemyObjectRepository,

# Version specific ports
LoadVersionPort: SqlAlchemyObjectVersionRepository,
SaveVersionPort: SqlAlchemyObjectVersionRepository,

# Permission specific ports
LoadPermissionPort:        SqlAlchemyObjectPermissionRepository,
SavePermissionPort:        SqlAlchemyObjectPermissionRepository,
LoadSubjectPermissionPort: SqlAlchemySubjectPermissionRepository,

# Audit specific port
SaveAuditPort: SqlAlchemyObjectAuditRepository,
```

### 7.2 Đảm bảo repository implementations có đủ methods

Sau khi thêm bindings, các SqlAlchemy repos phải implement tất cả methods của port tương ứng.

Kiểm tra:
- `SqlAlchemyObjectRepository` có `find_by_id()`, `find_by_owner()`, `exists()`, `save()`, `update()` không?
- `SqlAlchemyObjectPermissionRepository` có `find_by_subject_and_object()` không?
- `SqlAlchemySubjectPermissionRepository` có `find_by_subject()` và `has_permission()` không?
- `SqlAlchemyObjectAuditRepository` có `record()` với signature mới không?

Nếu thiếu → thêm vào repository tương ứng.

---

## Phase 8 — Use Cases mới (theo ra-soat-application-layer.md)

Sau khi các phase trên hoàn chỉnh, bổ sung thêm các use case còn thiếu theo ưu tiên:

### 8.1 Ưu tiên cao

| Use Case | File | Mô tả |
|----------|------|--------|
| `GrantSubjectPermissionUseCase` | `usecase/permission/GrantSubjectPermissionUseCase.py` | Cấp system permission cho Subject |
| `RevokeSubjectPermissionUseCase` | `usecase/permission/RevokeSubjectPermissionUseCase.py` | Thu hồi system permission |
| `GrantObjectPermissionUseCase` | `usecase/permission/GrantObjectPermissionUseCase.py` | Cấp ACL cho object |
| `RevokeObjectPermissionUseCase` | `usecase/permission/RevokeObjectPermissionUseCase.py` | Thu hồi ACL |

### 8.2 Ưu tiên vừa

| Use Case | File | Mô tả |
|----------|------|--------|
| `SyncSubjectInfoUseCase` | `usecase/subject/SyncSubjectInfoUseCase.py` | Đồng bộ subject cache từ event |
| `ChangeObjectVisibilityUseCase` | `usecase/object/ChangeObjectVisibilityUseCase.py` | Thay đổi visibility |
| `ListObjectsUseCase` | `usecase/object/ListObjectsUseCase.py` | Danh sách object theo owner/status |

### 8.3 Cập nhật dependency.py sau khi thêm use cases mới

Thêm scan cho các package mới:
```python
"app.application.usecase.permission",
"app.application.usecase.subject",
```

---

## Thứ tự thực hiện khuyến nghị

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7 → Phase 8
```

Lý do theo thứ tự này:
- Phase 1 (Domain) phải làm trước vì Phase 5 phụ thuộc vào nó
- Phase 3-4 (Audit/Command) phải làm trước Phase 5 (Use Cases)
- Phase 6 (Authorization) cần Phase 4 đã xong (commands có subject_type)
- Phase 7 (DI) làm cuối — binds tất cả together
- Phase 8 làm sau cùng khi core system ổn định

---

## Checklist tổng hợp

### Domain (Phase 1)
- [ ] `DataObject` thêm `created_at`, `updated_at` vào constructor
- [ ] `DataObject.is_public()` → trả `bool`
- [ ] `DataObject.can_transition_to(target)` → trả `bool`
- [ ] `DataObject.restore(now)` → trả `DataObject` mới
- [ ] `DataObject.archive(now)` → trả `DataObject` mới
- [ ] `DataObject.soft_delete(now)` → trả `DataObject` mới
- [ ] `DataObject.update_version(version_id, now)` → trả `DataObject` mới
- [ ] `ObjectPermission.has_capability(capability)` → trả `bool`

### Import (Phase 2)
- [ ] `CreateObjectUseCase` fix imports ObjectStatus, Role
- [ ] `RestoreObjectUseCase` fix import ObjectStatus
- [ ] `ArchiveObjectUseCase`, `DeleteObjectUseCase`, `PurgeObjectUseCase` rà soát imports
- [ ] `LoadPermissionPort` fix import path ObjectPermission

### Audit port/service (Phase 3)
- [ ] `SaveAuditPort.record()` thêm `actor_subject_type`, `actor_name`
- [ ] `AuditService.record()` thêm `actor_subject_type`, `actor_name`
- [ ] `SqlAlchemyObjectAuditRepository.record()` cập nhật tương ứng

### Commands/Queries (Phase 4)
- [ ] 7 object commands/queries thêm `requester_subject_type`, `requester_name`
- [ ] 4 version commands/queries thêm `requester_subject_type`, `requester_name`

### Use Cases — constructor calls (Phase 5)
- [ ] `CreateObjectUseCase`: DataObject thêm `owner_subject_type`
- [ ] `CreateObjectUseCase`: DataObject đổi `metadata_json` → `metadata`
- [ ] `CreateObjectUseCase`: ObjectVersion đổi `created_by` → `created_by_identity_id`, thêm `created_by_subject_type`
- [ ] `CreateObjectUseCase`: ObjectVersion wrap `ContentHash(...)`, `MimeType(...)`
- [ ] `CreateObjectUseCase`: ObjectPermission thêm `subject_type`
- [ ] `CreateObjectUseCase`: thêm `audit.record()` sau tạo thành công
- [ ] `CreateVersionUseCase`: tương tự ObjectVersion fixes
- [ ] Tất cả use cases: cập nhật `audit.record()` với args mới
- [ ] Tất cả use cases: cập nhật `require_capability()` với `requester_subject_type`

### Authorization (Phase 6)
- [ ] Tạo `LoadSubjectPermissionPort.py`
- [ ] `AuthorizationService` thêm `load_subject_permission` dependency
- [ ] `AuthorizationService.require_capability()` thêm `requester_subject_type` param
- [ ] Thêm System Permission check (layer đầu tiên)

### Dependency (Phase 7)
- [ ] `dependency.py` thêm bindings cho tất cả specific ports
- [ ] Verify SqlAlchemy repos có đủ methods

### Use Cases mới (Phase 8)
- [ ] `GrantSubjectPermissionUseCase`
- [ ] `RevokeSubjectPermissionUseCase`
- [ ] `GrantObjectPermissionUseCase`
- [ ] `RevokeObjectPermissionUseCase`
- [ ] `SyncSubjectInfoUseCase`
- [ ] `ChangeObjectVisibilityUseCase`
- [ ] `ListObjectsUseCase`
