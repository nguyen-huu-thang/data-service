# Kế hoạch triển khai Data Service

> Tài liệu này là roadmap thực thi — từng giai đoạn, từng file cần tạo, theo đúng thứ tự phụ thuộc.
>
> **Đọc trước khi bắt đầu**:
> - `D:\code\xime\xime framework\CLAUDE.md` — quy tắc framework bắt buộc
> - `.claude/docs/cay-thu-muc.md` — cấu trúc thư mục dự kiến
> - `.claude/rules/domain-coding-patterns.md` — code patterns cụ thể

---

## Trạng thái tổng quan

| Giai đoạn | Tên | Trạng thái |
| --- | --- | --- |
| Phase 0 | Chuẩn bị môi trường | ✅ Hoàn thành |
| Phase 1 | Domain Layer | ✅ Hoàn thành |
| Phase 2 | Port Interfaces | ✅ Hoàn thành |
| Phase 3 | Infrastructure — DB Schema | ✅ Hoàn thành |
| Phase 4 | Infrastructure — Repositories | ✅ Hoàn thành |
| Phase 5 | Infrastructure — Blob Storage | ✅ Hoàn thành |
| Phase 6 | Application — Authorization | ✅ Hoàn thành |
| Phase 7 | Application — Core Use Cases | ✅ Hoàn thành |
| Phase 8 | Security — JWT Verification | ✅ Hoàn thành |
| Phase 9 | API Layer — gRPC | ✅ Hoàn thành |
| Phase 10 | Config & Entry Point | ✅ Hoàn thành |
| Phase 11 | Advanced — Lifecycle & Versioning | ✅ Hoàn thành |
| Phase 12 | Advanced — Audit | ✅ Hoàn thành |
| Phase 13 | Testing | ✅ Hoàn thành |

Cập nhật `⬜ / 🔄 / ✅` theo tiến độ thực tế.

---

## Phase 0 — Chuẩn bị môi trường

**Mục tiêu**: Khởi tạo project Python, cài dependencies, tạo cấu trúc thư mục rỗng.

### 0.1 Đọc tài liệu bắt buộc

- [ ] Đọc `D:\code\xime\xime framework\CLAUDE.md`
- [ ] Đọc `D:\code\xime\xime framework\.claude\rules\coding.md`
- [ ] Nắm rõ DI scan/exclude/bind conventions

### 0.2 Cài đặt môi trường

```bash
# Python 3.12+
python -m venv .venv
.venv\Scripts\activate  # Windows

# BƯỚC 1: Cài Xime Framework từ local path
pip install -e "D:\code\xime\xime framework"

# BƯỚC 2: Cài các dependencies còn lại
pip install -r requirements.txt
```

`pyproject.toml` và `requirements.txt` đã tạo. ✅

### 0.3 Tạo cấu trúc thư mục

Tạo tất cả thư mục theo `.claude/docs/cay-thu-muc.md`. File rỗng ban đầu, chỉ cần `__init__.py` để Python nhận diện package.

**Thư mục cần tạo:**

```
app/
  api/grpc/external/object/
  api/grpc/external/permission/
  api/grpc/external/version/
  api/grpc/internal/
  api/grpc/mapper/
  application/dto/object/
  application/dto/permission/
  application/dto/version/
  application/port/inbound/
  application/port/outbound/object/
  application/port/outbound/permission/
  application/port/outbound/version/
  application/port/outbound/storage/
  application/usecase/object/
  application/usecase/permission/
  application/usecase/version/
  application/service/authorization/
  application/service/routing/
  application/service/lifecycle/
  application/service/audit/
  application/mapper/
  common/constants/
  common/exception/
  common/util/
  config/
  domain/object/
  domain/permission/
  domain/shard/
  integration/identity/
  integration/trust/key/
  integration/trust/certificate/
  infrastructure/persistence/entity/
  infrastructure/persistence/mapper/
  infrastructure/persistence/repository/object/
  infrastructure/persistence/repository/permission/
  infrastructure/persistence/repository/version/
  infrastructure/storage/minio/
  infrastructure/redis/
  infrastructure/event/publisher/
test/
```

### Kiểm tra Phase 0

- [ ] `python -c "import xime"` không lỗi (sau khi cài xime framework)
- [x] Tất cả package có `__init__.py` ✅ (71 files)

---

## Phase 1 — Domain Layer

**Mục tiêu**: Định nghĩa toàn bộ domain model — thuần Python, không phụ thuộc gì ngoài standard library.

> Domain package được **excluded khỏi DI**. Không import infrastructure/application vào domain.

### 1.1 Constants & Enums

**`app/common/constants/ObjectType.py`**

```python
from enum import StrEnum

class ObjectType(StrEnum):
    IMAGE    = "IMAGE"
    VIDEO    = "VIDEO"
    DOCUMENT = "DOCUMENT"
    ARCHIVE  = "ARCHIVE"
    DATASET  = "DATASET"
```

Tương tự cho:

- `app/common/constants/ObjectStatus.py` → `ACTIVE`, `ARCHIVED`, `SOFT_DELETED`, `PURGED`
- `app/common/constants/Visibility.py` → `PRIVATE`, `INTERNAL`, `PUBLIC`
- `app/common/constants/Capability.py` → `READ`, `WRITE`, `DELETE`, `SHARE`, `DOWNLOAD`, `COMMENT`
- `app/common/constants/Role.py` → `OWNER`, `EDITOR`, `CONTRIBUTOR`, `VIEWER`

### 1.2 Exceptions

**`app/common/exception/`**

```python
# ObjectNotFoundException.py
class ObjectNotFoundException(Exception):
    def __init__(self, object_id: bytes):
        super().__init__(f"Object not found: {object_id.hex()}")

# PermissionDeniedException.py
class PermissionDeniedException(Exception):
    pass

# ObjectAlreadyDeletedException.py
class ObjectAlreadyDeletedException(Exception):
    pass

# InvalidShardException.py
class InvalidShardException(Exception):
    pass
```

### 1.3 ID Utility

**`app/common/util/IdGenerator.py`**

```python
import os
import struct
import time

KSUID_EPOCH = 1_400_000_000

def generate_id() -> bytes:
    ts = int(time.time()) - KSUID_EPOCH
    return struct.pack('>I', ts) + os.urandom(20)  # 24 bytes

def id_to_hex(ksuid: bytes) -> str:
    return ksuid.hex()
```

### 1.4 Domain Models

**`app/domain/object/DataObject.py`**

```python
from dataclasses import dataclass, replace
from datetime import datetime
from app.common.constants.ObjectStatus import ObjectStatus
from app.common.constants.ObjectType import ObjectType
from app.common.constants.Visibility import Visibility

@dataclass(frozen=True)
class DataObject:
    object_id: bytes                  # KSUID 24 bytes
    owner_identity_id: bytes          # KSUID 24 bytes
    tenant_id: str | None
    shard_id: str                     # VD: DATA_SHARD_01
    object_type: ObjectType
    visibility: Visibility
    status: ObjectStatus
    storage_provider: str             # MINIO, S3, FILESYSTEM
    storage_pointer: str              # địa chỉ blob
    metadata_json: dict
    permission_version: int
    created_at: datetime
    updated_at: datetime
    current_version_id: bytes | None = None

    def archive(self, now: datetime) -> 'DataObject':
        return replace(self, status=ObjectStatus.ARCHIVED, updated_at=now)

    def soft_delete(self, now: datetime) -> 'DataObject':
        return replace(self, status=ObjectStatus.SOFT_DELETED, updated_at=now)

    def restore(self, now: datetime) -> 'DataObject':
        return replace(self, status=ObjectStatus.ACTIVE, updated_at=now)

    def is_accessible(self) -> bool:
        return self.status == ObjectStatus.ACTIVE

    def is_public(self) -> bool:
        return self.visibility == Visibility.PUBLIC
```

**`app/domain/object/ObjectVersion.py`**

```python
@dataclass(frozen=True)
class ObjectVersion:
    version_id: bytes
    object_id: bytes
    version_number: int
    storage_pointer: str
    content_hash: str          # SHA256
    content_size: int          # bytes
    mime_type: str
    created_by: bytes          # identity_id
    created_at: datetime
```

**`app/domain/permission/ObjectPermission.py`**

```python
from app.common.constants.Role import Role
from app.common.constants.Capability import Capability

ROLE_CAPABILITIES: dict[Role, set[Capability]] = {
    Role.OWNER:       {Capability.READ, Capability.WRITE, Capability.DELETE,
                       Capability.SHARE, Capability.DOWNLOAD, Capability.COMMENT},
    Role.EDITOR:      {Capability.READ, Capability.WRITE, Capability.DOWNLOAD, Capability.COMMENT},
    Role.CONTRIBUTOR: {Capability.READ, Capability.WRITE, Capability.COMMENT},
    Role.VIEWER:      {Capability.READ, Capability.DOWNLOAD},
}

@dataclass(frozen=True)
class ObjectPermission:
    permission_id: bytes
    object_id: bytes
    subject_identity_id: bytes
    role: Role
    created_at: datetime

    def has_capability(self, capability: Capability) -> bool:
        return capability in ROLE_CAPABILITIES.get(self.role, set())
```

**`app/domain/shard/ShardInfo.py`**

```python
@dataclass(frozen=True)
class ShardInfo:
    shard_id: str
    host: str
    port: int
    is_local: bool
```

### Kiểm tra Phase 1

- [x] Tất cả domain model dùng `@dataclass(frozen=True)` ✅
- [x] State change method return instance mới (không mutate) ✅
- [x] Không có import nào từ `infrastructure`, `application`, `sqlalchemy` ✅
- [x] `ROLE_CAPABILITIES` đúng theo thiết kế ✅ (dùng `frozenset` thay `set` cho immutability)

---

## Phase 2 — Port Interfaces

**Mục tiêu**: Định nghĩa contract "cần gì từ bên ngoài" — sử dụng `Protocol`.

> Port package được **excluded khỏi DI**. Port là interface, không phải implementation.

### 2.1 Object Ports

**`app/application/port/outbound/object/LoadObjectPort.py`**

```python
from typing import Protocol
from app.domain.object.DataObject import DataObject

class LoadObjectPort(Protocol):
    async def find_by_id(self, object_id: bytes) -> DataObject | None: ...
    async def find_by_owner(self, owner_identity_id: bytes, tenant_id: str | None) -> list[DataObject]: ...
    async def exists(self, object_id: bytes) -> bool: ...
```

**`app/application/port/outbound/object/SaveObjectPort.py`**

```python
class SaveObjectPort(Protocol):
    async def save(self, obj: DataObject) -> None: ...
    async def update(self, obj: DataObject) -> None: ...
```

### 2.2 Permission Ports

**`app/application/port/outbound/permission/LoadPermissionPort.py`**

```python
class LoadPermissionPort(Protocol):
    async def find_by_object(self, object_id: bytes) -> list[ObjectPermission]: ...
    async def find_by_subject_and_object(
        self, subject_id: bytes, object_id: bytes
    ) -> ObjectPermission | None: ...
```

**`app/application/port/outbound/permission/SavePermissionPort.py`**

```python
class SavePermissionPort(Protocol):
    async def save(self, permission: ObjectPermission) -> None: ...
    async def delete(self, permission_id: bytes) -> None: ...
```

### 2.3 Version Port

**`app/application/port/outbound/version/LoadVersionPort.py`**
**`app/application/port/outbound/version/SaveVersionPort.py`**

### 2.4 Blob Storage Port

**`app/application/port/outbound/storage/BlobStoragePort.py`**

```python
class BlobStoragePort(Protocol):
    async def upload(self, pointer: str, data: bytes, content_type: str) -> None: ...
    async def download(self, pointer: str) -> bytes: ...
    async def delete(self, pointer: str) -> None: ...
    async def exists(self, pointer: str) -> bool: ...
    async def generate_pointer(self, owner_id: bytes, object_id: bytes, filename: str) -> str: ...
```

### 2.5 Audit Port (tùy chọn)

**`app/application/port/outbound/audit/SaveAuditPort.py`**

```python
class SaveAuditPort(Protocol):
    async def record(self, object_id: bytes, actor_id: bytes, action: str) -> None: ...
```

### Kiểm tra Phase 2

- [x] Tất cả port dùng `Protocol` (không phải ABC) ✅
- [x] Method signature rõ ràng với type hint đầy đủ ✅
- [x] Không có logic implementation trong port ✅

---

## Phase 3 — Infrastructure: DB Schema

**Mục tiêu**: Định nghĩa SQLAlchemy ORM entities và setup Alembic migration.

### 3.1 SQLAlchemy Base Config

**`app/config/database.py`**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

### 3.2 ORM Entities

**`app/infrastructure/persistence/entity/DataObjectEntity.py`**

```python
from sqlalchemy import Column, LargeBinary, String, Integer, DateTime, JSON
from app.config.database import Base

class DataObjectEntity(Base):
    __tablename__ = 'data_object'

    object_id          = Column(LargeBinary(24), primary_key=True)
    owner_identity_id  = Column(LargeBinary(24), nullable=False, index=True)
    tenant_id          = Column(String(100), nullable=True)
    shard_id           = Column(String(20),  nullable=False)
    object_type        = Column(String(20),  nullable=False)
    visibility         = Column(String(20),  nullable=False)
    status             = Column(String(20),  nullable=False, index=True)
    storage_provider   = Column(String(20),  nullable=False)
    storage_pointer    = Column(String(500), nullable=False)
    metadata_json      = Column(JSON,        nullable=True)
    permission_version = Column(Integer,     nullable=False, default=1)
    current_version_id = Column(LargeBinary(24), nullable=True)
    created_at         = Column(DateTime(timezone=True), nullable=False)
    updated_at         = Column(DateTime(timezone=True), nullable=False)
```

Tương tự cho:

- `ObjectVersionEntity.py`
- `ObjectPermissionEntity.py`
- `ObjectAuditEntity.py`

### 3.3 Alembic Setup

```bash
alembic init migrations
```

Tạo migration đầu tiên cho 4 bảng MVP:

- `data_object`
- `object_version`
- `object_permission`
- `object_audit`

### Kiểm tra Phase 3

- [x] Entity không có business logic ✅
- [x] Tất cả `binary(24)` dùng `LargeBinary(24)` ✅
- [x] Index theo thiết kế: `(owner_identity_id, tenant_id, status, object_type)` ✅
- [ ] Migration chạy được: `DATABASE_URL=... alembic upgrade head` (cần PostgreSQL chạy)

---

## Phase 4 — Infrastructure: Repositories

**Mục tiêu**: Implement các Port interfaces bằng SQLAlchemy.

> Repository nằm trong `infrastructure/` → **được DI scan tự động**.
> Constructor nhận session qua Xime Framework (không tự tạo session).

### 4.1 Object Repository

**`app/infrastructure/persistence/repository/object/SqlAlchemyObjectRepository.py`**

```python
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort

class SqlAlchemyObjectRepository:
    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    async def find_by_id(self, object_id: bytes) -> DataObject | None:
        async with self._session_factory() as session:
            entity = await session.get(DataObjectEntity, object_id)
            if entity is None:
                return None
            return DataObjectMapper.to_domain(entity)

    async def save(self, obj: DataObject) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                entity = DataObjectMapper.to_entity(obj)
                session.add(entity)
```

### 4.2 Entity ↔ Domain Mapper

**`app/infrastructure/persistence/mapper/DataObjectMapper.py`**

```python
class DataObjectMapper:
    @staticmethod
    def to_domain(entity: DataObjectEntity) -> DataObject:
        return DataObject(
            object_id=entity.object_id,
            owner_identity_id=entity.owner_identity_id,
            status=ObjectStatus(entity.status),
            # ...
        )

    @staticmethod
    def to_entity(domain: DataObject) -> DataObjectEntity:
        return DataObjectEntity(
            object_id=domain.object_id,
            status=domain.status.value,
            # ...
        )
```

### 4.3 Permission Repository

**`app/infrastructure/persistence/repository/permission/SqlAlchemyPermissionRepository.py`**

Tương tự pattern trên.

### Kiểm tra Phase 4

- [x] Repository không có business logic ✅
- [x] Mapper tách riêng (không nằm trong repository) ✅
- [x] Không import domain từ entity (chỉ entity biết về domain qua mapper) ✅

---

## Phase 5 — Infrastructure: Blob Storage

**Mục tiêu**: Implement `BlobStoragePort` với MinIO.

**`app/infrastructure/storage/minio/MinioStorageAdapter.py`**

```python
from minio import Minio
from app.application.port.outbound.storage.BlobStoragePort import BlobStoragePort

class MinioStorageAdapter:
    def __init__(self, minio_client: Minio, bucket_name: str) -> None:
        self._client = minio_client
        self._bucket = bucket_name

    async def upload(self, pointer: str, data: bytes, content_type: str) -> None:
        # minio.put_object(...)

    async def download(self, pointer: str) -> bytes:
        # minio.get_object(...)

    async def generate_pointer(self, owner_id: bytes, object_id: bytes, filename: str) -> str:
        owner_hex = owner_id.hex()[:8]
        object_hex = object_id.hex()
        return f"{owner_hex}/{object_hex}/{filename}"
```

### Kiểm tra Phase 5

- [x] `generate_pointer()` deterministic — cùng input → cùng output ✅
- [x] Không lưu binary vào DB (chỉ lưu pointer) ✅
- [x] Error handling đầy đủ cho minio exceptions ✅ (S3Error.code == "NoSuchKey" handled)

---

## Phase 6 — Application: Authorization Service

**Mục tiêu**: Service đánh giá capability từ ACL — core security logic.

**`app/application/service/authorization/AuthorizationService.py`**

```python
from app.application.port.outbound.permission.LoadPermissionPort import LoadPermissionPort
from app.common.constants.Capability import Capability
from app.common.constants.Visibility import Visibility
from app.common.exception.PermissionDeniedException import PermissionDeniedException
from app.domain.object.DataObject import DataObject

class AuthorizationService:
    def __init__(self, load_permission_port: LoadPermissionPort) -> None:
        self._load_permission = load_permission_port

    async def require_capability(
        self,
        requester_identity_id: bytes,
        obj: DataObject,
        capability: Capability,
    ) -> None:
        # 1. PUBLIC object → READ/DOWNLOAD không cần check ACL
        if obj.is_public() and capability in (Capability.READ, Capability.DOWNLOAD):
            return

        # 2. Owner luôn có toàn quyền
        if obj.owner_identity_id == requester_identity_id:
            return

        # 3. Load ACL
        permission = await self._load_permission.find_by_subject_and_object(
            requester_identity_id, obj.object_id
        )
        if permission is None or not permission.has_capability(capability):
            raise PermissionDeniedException()
```

### Kiểm tra Phase 6

- [x] Owner bypass ACL ✅
- [x] PUBLIC object bypass READ/DOWNLOAD ✅
- [x] `PermissionDeniedException` raised khi không có quyền ✅
- [x] Không có DB logic trong service này — chỉ gọi port ✅

---

## Phase 7 — Application: Core Use Cases

**Mục tiêu**: 4 use case cốt lõi — tạo, đọc, tải, xóa object.

> Đây là **MVP** — đủ để test end-to-end flow hoàn chỉnh.

### 7.1 CreateObjectUseCase

**`app/application/usecase/object/CreateObjectUseCase.py`**

```
Input: CreateObjectCommand {
    requester_identity_id, tenant_id, object_type, visibility,
    filename, content_type, data (bytes)
}

Steps:
  1. Generate object_id (KSUID 24 bytes)
  2. Compute shard_id = routing_service.compute_shard(requester_identity_id)
  3. Generate storage_pointer
  4. Upload blob → BlobStoragePort.upload()
  5. Compute SHA256 content_hash
  6. Create DataObject domain model (status=ACTIVE)
  7. Create ObjectVersion (version_number=1, content_hash, content_size)
  8. Create ObjectPermission (subject=requester, role=OWNER)
  9. Save DataObject → SaveObjectPort.save()
  10. Save ObjectVersion → SaveVersionPort.save()
  11. Save ObjectPermission → SavePermissionPort.save()
  12. Return CreateObjectResult { object_id, shard_id, storage_pointer }

Transaction: bước 4 (blob) trước transaction DB. Nếu DB fail → cần cleanup blob.
```

### 7.2 GetObjectUseCase

**`app/application/usecase/object/GetObjectUseCase.py`**

```
Input: GetObjectQuery { requester_identity_id, object_id }

Steps:
  1. Load DataObject → LoadObjectPort.find_by_id()
  2. Nếu không tìm thấy → raise ObjectNotFoundException
  3. Nếu status == PURGED → raise ObjectNotFoundException
  4. AuthorizationService.require_capability(requester, obj, READ)
  5. Ghi audit: READ
  6. Return DataObject metadata (không trả blob)
```

### 7.3 DownloadObjectUseCase

**`app/application/usecase/object/DownloadObjectUseCase.py`**

```
Input: DownloadObjectQuery { requester_identity_id, object_id }

Steps:
  1. Load DataObject (như GetObject)
  2. AuthorizationService.require_capability(requester, obj, DOWNLOAD)
  3. BlobStoragePort.download(obj.storage_pointer)
  4. Ghi audit: DOWNLOAD
  5. Return blob bytes + mime_type
```

### 7.4 DeleteObjectUseCase (Soft Delete)

**`app/application/usecase/object/DeleteObjectUseCase.py`**

```
Input: DeleteObjectCommand { requester_identity_id, object_id }

Steps:
  1. Load DataObject
  2. AuthorizationService.require_capability(requester, obj, DELETE)
  3. obj = obj.soft_delete(now=datetime.now(utc))
  4. SaveObjectPort.update(obj)
  5. Ghi audit: DELETE
```

### Kiểm tra Phase 7

- [x] Authorization check trước khi mọi thao tác ✅
- [x] Audit ghi sau mỗi thao tác thành công ✅ (AuditService swallows exceptions)
- [x] Không có logic DB trong UseCase — chỉ gọi port ✅
- [x] CreateObject: nếu DB fail sau khi upload blob → log warning với object_id + pointer ✅
- [x] Transaction scope rõ ràng ✅ (blob IO ngoài tx, tất cả DB ops trong `async with self._tx()`)

**Thay đổi so với plan gốc (Phase 4):**
- Repositories đã được sửa để dùng `AsyncSessionFactory.current()` thay vì `session_factory()`
- Pattern này đảm bảo tất cả repo calls trong cùng transaction context dùng chung một session

---

## Phase 8 — Security: JWT Verification

**Mục tiêu**: Verify JWT từ client bằng public key từ Trust Service.

### 8.1 KeyContext Domain Model

**`app/domain/key/KeyContext.py`**

```python
@dataclass(frozen=True)
class KeyContext:
    key_id: str
    public_key: str
    algorithm: str              # RS256, ES256, EdDSA
    activate_at: datetime
    expires_at: datetime

    def can_verify(self, now: datetime) -> bool:
        return now < self.expires_at
```

### 8.2 VerificationKeyCache

**`app/integration/trust/key/VerificationKeyCache.py`**

```python
from threading import Lock

class VerificationKeyCache:
    def __init__(self) -> None:
        self._cache: dict[str, KeyContext] = {}
        self._lock = Lock()

    def resolve(self, key_id: str, now: datetime) -> KeyContext | None:
        key = self._cache.get(key_id)
        return key if key and key.can_verify(now) else None

    def update(self, keys: list[KeyContext]) -> None:
        with self._lock:
            for key in keys:
                self._cache[key.key_id] = key

    def clean_expired(self, now: datetime) -> None:
        with self._lock:
            self._cache = {k: v for k, v in self._cache.items() if v.can_verify(now)}
```

### 8.3 Trust Service gRPC Client

**`app/integration/trust/key/TrustKeyClient.py`**

```python
class TrustKeyClient:
    def __init__(self, trust_channel) -> None:
        self._stub = KeyDistributionStub(trust_channel)

    async def fetch_verification_keys(
        self, signer_service_id: str, verifier_service_id: str
    ) -> list[KeyContext]:
        response = await self._stub.GetVerificationKeys(
            GetVerificationKeysRequest(
                signer_service_id=signer_service_id,
                verifier_service_id=verifier_service_id,
            )
        )
        return [self._map_key(k) for k in response.keys]
```

### 8.4 JWT Verification Service

**`app/application/service/authorization/JwtVerificationService.py`**

```python
import jwt  # PyJWT

class JwtVerificationService:
    def __init__(
        self,
        key_cache: VerificationKeyCache,
        trust_key_client: TrustKeyClient,
        service_id: str,    # "data-service"
    ) -> None:
        self._cache = key_cache
        self._trust = trust_key_client
        self._service_id = service_id

    async def verify(self, token: str) -> VerifiedClaims:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        key_ctx = self._cache.resolve(kid, now=datetime.now(utc))
        if key_ctx is None:
            # Sync từ Trust Service
            keys = await self._trust.fetch_verification_keys(
                signer_service_id="identity-service",
                verifier_service_id=self._service_id,
            )
            self._cache.update(keys)
            key_ctx = self._cache.resolve(kid, now=datetime.now(utc))

        if key_ctx is None:
            raise InvalidTokenException("Unknown key")

        payload = jwt.decode(
            token,
            key_ctx.public_key,
            algorithms=[key_ctx.algorithm],
            audience=self._service_id,
            issuer="identity-service",
        )

        identity_id_hex = payload["sub"]
        return VerifiedClaims(
            identity_id=bytes.fromhex(identity_id_hex),
            token_version=payload["token_version"],
        )
```

### Kiểm tra Phase 8

- [ ] Verify `aud` chứa `"data-service"`
- [ ] Verify `iss == "identity-service"`
- [ ] Verify `exp > now`
- [ ] Cache miss → sync từ Trust, retry 1 lần
- [ ] Cache có clean expired keys theo định kỳ (background task)

---

## Phase 9 — API Layer: gRPC

**Mục tiêu**: Expose các use case qua gRPC.

### 9.1 Proto Definitions

Tạo file `.proto` trong `app/api/grpc/`:

**`object_service.proto`**

```protobuf
service ObjectService {
  rpc CreateObject (CreateObjectRequest) returns (CreateObjectResponse);
  rpc GetObject    (GetObjectRequest)    returns (GetObjectResponse);
  rpc DeleteObject (DeleteObjectRequest) returns (DeleteObjectResponse);
}

message CreateObjectRequest {
  string  requester_identity_id = 1;
  string  object_type           = 2;
  string  visibility            = 3;
  string  filename              = 4;
  string  content_type          = 5;
  bytes   data                  = 6;
  string  tenant_id             = 7;
}
```

**`permission_service.proto`**

```protobuf
service PermissionService {
  rpc GrantPermission  (GrantPermissionRequest)  returns (GrantPermissionResponse);
  rpc RevokePermission (RevokePermissionRequest) returns (RevokePermissionResponse);
}
```

Generate Python stubs:

```bash
python -m grpc_tools.protoc \
    -I app/api/grpc/proto \
    --python_out=app/api/grpc/generated \
    --grpc_python_out=app/api/grpc/generated \
    app/api/grpc/proto/*.proto
```

### 9.2 gRPC Handler

**`app/api/grpc/external/object/ObjectGrpcHandler.py`**

```python
class ObjectGrpcHandler(ObjectServiceServicer):
    def __init__(
        self,
        create_object_use_case: CreateObjectUseCase,
        get_object_use_case: GetObjectUseCase,
        delete_object_use_case: DeleteObjectUseCase,
        jwt_verification_service: JwtVerificationService,
        mapper: ObjectGrpcMapper,
    ) -> None:
        # constructor injection
        ...

    async def CreateObject(self, request, context):
        try:
            claims = await self.jwt_verification_service.verify(
                self._extract_token(context)
            )
            command = self._mapper.to_create_command(request, claims.identity_id)
            result = await self._create_use_case.execute(command)
            return self._mapper.to_create_response(result)
        except PermissionDeniedException:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, "Permission denied")
        except ObjectNotFoundException:
            await context.abort(grpc.StatusCode.NOT_FOUND, "Object not found")
        except Exception:
            await context.abort(grpc.StatusCode.INTERNAL, "Internal error")
```

### 9.3 gRPC Mapper

**`app/api/grpc/mapper/ObjectGrpcMapper.py`**

- `to_create_command(request, identity_id)` → `CreateObjectCommand`
- `to_create_response(result)` → protobuf response
- Mapper là **utility class**, không phải service — không inject vào DI

### Kiểm tra Phase 9

- [ ] JWT verify ở đầu mỗi handler
- [ ] Exception mapping: domain exception → gRPC status code
- [ ] Không có business logic trong handler/mapper

---

## Phase 10 — Config & Entry Point

**Mục tiêu**: Wiring toàn bộ application, khởi động server.

### 10.1 DI Configuration

**`app/config/dependency.py`**

```python
from xime import dependency
from app.application.port.outbound.storage.BlobStoragePort import BlobStoragePort
from app.infrastructure.storage.minio.MinioStorageAdapter import MinioStorageAdapter
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.infrastructure.persistence.repository.object.SqlAlchemyObjectRepository \
    import SqlAlchemyObjectRepository
# ... các import khác

dependency.scan(
    "app.application.usecase",
    "app.application.service",
    "app.infrastructure.persistence.repository",
    "app.infrastructure.storage",
    "app.infrastructure.event",
    "app.integration.trust",
    "app.api.grpc.external",
    "app.api.grpc.internal",
)

dependency.exclude(
    "app.domain",
    "app.common.constants",
    "app.common.exception",
    "app.application.port",
    "app.application.dto",
    "app.application.mapper",
    "app.infrastructure.persistence.entity",
    "app.infrastructure.persistence.mapper",
    "app.api.grpc.mapper",
)

dependency.bind({
    LoadObjectPort:      SqlAlchemyObjectRepository,
    SaveObjectPort:      SqlAlchemyObjectRepository,
    LoadPermissionPort:  SqlAlchemyPermissionRepository,
    SavePermissionPort:  SqlAlchemyPermissionRepository,
    BlobStoragePort:     MinioStorageAdapter,
})
```

### 10.2 Entry Point

**`app/main.py`**

```python
from xime import Application

app = Application()

if __name__ == "__main__":
    app.run()
```

### Kiểm tra Phase 10

- [ ] `python app/main.py` khởi động không lỗi
- [ ] DI resolve toàn bộ dependency (startup fail = thiếu binding)
- [ ] Không còn lỗi circular dependency
- [ ] gRPC server listen thành công

---

## Phase 11 — Advanced: Lifecycle & Versioning

**Mục tiêu**: Hoàn thiện vòng đời object (archive, restore, purge) và hệ thống versioning (tạo version mới, xem lịch sử, tải version cụ thể).

**Điều kiện**: Phase 10 đã hoạt động ổn định — gRPC server khởi động được, MVP use case chạy end-to-end.

---

### 11.1 Domain — Transition Guard

Thêm lifecycle transition guard vào `DataObject` để đảm bảo state machine hợp lệ.

**Cập nhật `app/domain/object/DataObject.py`**

```python
from app.common.constants.ObjectStatus import ObjectStatus

# Transition hợp lệ — chỉ cho phép các chuyển đổi này
VALID_TRANSITIONS: dict[ObjectStatus, set[ObjectStatus]] = {
    ObjectStatus.ACTIVE:       {ObjectStatus.ARCHIVED, ObjectStatus.SOFT_DELETED},
    ObjectStatus.ARCHIVED:     {ObjectStatus.ACTIVE,   ObjectStatus.SOFT_DELETED},
    ObjectStatus.SOFT_DELETED: {ObjectStatus.ACTIVE,   ObjectStatus.PURGED},
    ObjectStatus.PURGED:       set(),  # terminal state — không đổi được nữa
}

@dataclass(frozen=True)
class DataObject:
    # ... (các field giữ nguyên) ...

    def can_transition_to(self, target: ObjectStatus) -> bool:
        return target in VALID_TRANSITIONS.get(self.status, set())

    def archive(self, now: datetime) -> 'DataObject':
        # Caller phải check can_transition_to() trước khi gọi
        return replace(self, status=ObjectStatus.ARCHIVED, updated_at=now)

    def soft_delete(self, now: datetime) -> 'DataObject':
        return replace(self, status=ObjectStatus.SOFT_DELETED, updated_at=now)

    def restore(self, now: datetime) -> 'DataObject':
        return replace(self, status=ObjectStatus.ACTIVE, updated_at=now)

    def purge(self, now: datetime) -> 'DataObject':
        # Đánh dấu PURGED — không xóa row (giữ audit trail)
        return replace(self, status=ObjectStatus.PURGED, updated_at=now)

    def update_version(self, version_id: bytes, now: datetime) -> 'DataObject':
        return replace(self, current_version_id=version_id, updated_at=now)
```

**Thêm exception mới vào `app/common/exception/`**

```python
# InvalidObjectStateException.py
class InvalidObjectStateException(Exception):
    def __init__(self, current: str, target: str):
        super().__init__(f"Cannot transition from {current} to {target}")
```

---

### 11.2 DTOs — Commands & Queries

> DTOs là data class thuần — excluded khỏi DI.

**`app/application/dto/object/ArchiveObjectCommand.py`**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ArchiveObjectCommand:
    requester_identity_id: bytes
    object_id: bytes
```

Tương tự cho:
- `RestoreObjectCommand.py` — `{requester_identity_id, object_id}`
- `PurgeObjectCommand.py` — `{requester_identity_id, object_id}`

**`app/application/dto/version/CreateVersionCommand.py`**

```python
@dataclass(frozen=True)
class CreateVersionCommand:
    requester_identity_id: bytes
    object_id: bytes
    filename: str
    content_type: str        # MIME type, VD: image/jpeg
    data: bytes              # binary content
```

Tương tự cho:
- `GetVersionQuery.py` — `{requester_identity_id, object_id, version_id}`
- `ListVersionsQuery.py` — `{requester_identity_id, object_id}`
- `DownloadVersionQuery.py` — `{requester_identity_id, object_id, version_id}`

---

### 11.3 Port Interfaces — Version

**`app/application/port/outbound/version/LoadVersionPort.py`**

```python
from typing import Protocol
from app.domain.object.ObjectVersion import ObjectVersion

class LoadVersionPort(Protocol):
    async def find_by_id(self, version_id: bytes) -> ObjectVersion | None: ...
    async def find_by_object(self, object_id: bytes) -> list[ObjectVersion]: ...
    async def find_max_version_number(self, object_id: bytes) -> int: ...
        # Trả 0 nếu chưa có version nào
```

**`app/application/port/outbound/version/SaveVersionPort.py`**

```python
class SaveVersionPort(Protocol):
    async def save(self, version: ObjectVersion) -> None: ...
```

**Thêm method vào `SaveObjectPort`** (cần để purge xóa blob của nhiều version):

```python
# Không cần thêm — chỉ cần load versions rồi xóa từng blob qua BlobStoragePort
```

---

### 11.4 Repository — Version

**`app/infrastructure/persistence/repository/version/SqlAlchemyVersionRepository.py`**

```python
from app.application.port.outbound.version.LoadVersionPort import LoadVersionPort
from app.application.port.outbound.version.SaveVersionPort import SaveVersionPort
from app.infrastructure.persistence.mapper.ObjectVersionMapper import ObjectVersionMapper
from app.infrastructure.persistence.entity.ObjectVersionEntity import ObjectVersionEntity
from sqlalchemy import select, func

class SqlAlchemyVersionRepository:
    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    async def find_by_id(self, version_id: bytes) -> ObjectVersion | None:
        async with self._session_factory.current() as session:
            entity = await session.get(ObjectVersionEntity, version_id)
            return ObjectVersionMapper.to_domain(entity) if entity else None

    async def find_by_object(self, object_id: bytes) -> list[ObjectVersion]:
        async with self._session_factory.current() as session:
            stmt = (
                select(ObjectVersionEntity)
                .where(ObjectVersionEntity.object_id == object_id)
                .order_by(ObjectVersionEntity.version_number.desc())
            )
            result = await session.execute(stmt)
            return [ObjectVersionMapper.to_domain(e) for e in result.scalars()]

    async def find_max_version_number(self, object_id: bytes) -> int:
        async with self._session_factory.current() as session:
            stmt = select(func.max(ObjectVersionEntity.version_number)).where(
                ObjectVersionEntity.object_id == object_id
            )
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def save(self, version: ObjectVersion) -> None:
        async with self._session_factory.current() as session:
            entity = ObjectVersionMapper.to_entity(version)
            session.add(entity)
```

**`app/infrastructure/persistence/mapper/ObjectVersionMapper.py`**

```python
from app.domain.object.ObjectVersion import ObjectVersion
from app.infrastructure.persistence.entity.ObjectVersionEntity import ObjectVersionEntity
from datetime import timezone

class ObjectVersionMapper:
    @staticmethod
    def to_domain(entity: ObjectVersionEntity) -> ObjectVersion:
        return ObjectVersion(
            version_id=entity.id,
            object_id=entity.object_id,
            version_number=entity.version_number,
            storage_pointer=entity.storage_pointer,
            content_hash=entity.content_hash,
            content_size=entity.content_size,
            mime_type=entity.mime_type,
            created_by=entity.created_by,
            created_at=entity.created_at.replace(tzinfo=timezone.utc),
        )

    @staticmethod
    def to_entity(domain: ObjectVersion) -> ObjectVersionEntity:
        return ObjectVersionEntity(
            id=domain.version_id,
            object_id=domain.object_id,
            version_number=domain.version_number,
            storage_pointer=domain.storage_pointer,
            content_hash=domain.content_hash,
            content_size=domain.content_size,
            mime_type=domain.mime_type,
            created_by=domain.created_by,
            created_at=domain.created_at,
        )
```

---

### 11.5 Lifecycle Use Cases

#### ArchiveObjectUseCase

**`app/application/usecase/object/ArchiveObjectUseCase.py`**

```python
from datetime import datetime, timezone
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.application.service.audit.AuditService import AuditService
from app.application.dto.object.ArchiveObjectCommand import ArchiveObjectCommand
from app.common.constants.Capability import Capability
from app.common.constants.ObjectStatus import ObjectStatus
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.common.exception.InvalidObjectStateException import InvalidObjectStateException

class ArchiveObjectUseCase:
    def __init__(
        self,
        load_object_port: LoadObjectPort,
        save_object_port: SaveObjectPort,
        authorization_service: AuthorizationService,
        audit_service: AuditService,
    ) -> None:
        self._load = load_object_port
        self._save = save_object_port
        self._auth = authorization_service
        self._audit = audit_service

    async def execute(self, command: ArchiveObjectCommand) -> None:
        obj = await self._load.find_by_id(command.object_id)
        if obj is None:
            raise ObjectNotFoundException(command.object_id)

        if not obj.can_transition_to(ObjectStatus.ARCHIVED):
            raise InvalidObjectStateException(obj.status.value, ObjectStatus.ARCHIVED.value)

        await self._auth.require_capability(
            command.requester_identity_id, obj, Capability.DELETE
        )

        now = datetime.now(timezone.utc)
        updated = obj.archive(now)
        await self._save.update(updated)
        await self._audit.record(obj.object_id, command.requester_identity_id, "ARCHIVE")
```

#### RestoreObjectUseCase

**`app/application/usecase/object/RestoreObjectUseCase.py`**

```python
class RestoreObjectUseCase:
    def __init__(
        self,
        load_object_port: LoadObjectPort,
        save_object_port: SaveObjectPort,
        audit_service: AuditService,
    ) -> None:
        self._load = load_object_port
        self._save = save_object_port
        self._audit = audit_service

    async def execute(self, command: RestoreObjectCommand) -> None:
        obj = await self._load.find_by_id(command.object_id)
        if obj is None:
            raise ObjectNotFoundException(command.object_id)

        if not obj.can_transition_to(ObjectStatus.ACTIVE):
            raise InvalidObjectStateException(obj.status.value, ObjectStatus.ACTIVE.value)

        # Chỉ OWNER mới restore được — không dùng capability, check ownership trực tiếp
        if obj.owner_identity_id != command.requester_identity_id:
            raise PermissionDeniedException()

        now = datetime.now(timezone.utc)
        updated = obj.restore(now)
        await self._save.update(updated)
        await self._audit.record(obj.object_id, command.requester_identity_id, "RESTORE")
```

#### PurgeObjectUseCase

**`app/application/usecase/object/PurgeObjectUseCase.py`**

```python
import logging
from app.application.port.outbound.version.LoadVersionPort import LoadVersionPort
from app.application.port.outbound.storage.BlobStoragePort import BlobStoragePort

_log = logging.getLogger(__name__)

class PurgeObjectUseCase:
    def __init__(
        self,
        load_object_port: LoadObjectPort,
        save_object_port: SaveObjectPort,
        load_version_port: LoadVersionPort,
        blob_storage_port: BlobStoragePort,
        audit_service: AuditService,
    ) -> None:
        self._load = load_object_port
        self._save = save_object_port
        self._load_version = load_version_port
        self._blob = blob_storage_port
        self._audit = audit_service

    async def execute(self, command: PurgeObjectCommand) -> None:
        obj = await self._load.find_by_id(command.object_id)
        if obj is None:
            raise ObjectNotFoundException(command.object_id)

        # Guard: chỉ SOFT_DELETED mới purge được
        if not obj.can_transition_to(ObjectStatus.PURGED):
            raise InvalidObjectStateException(obj.status.value, ObjectStatus.PURGED.value)

        # Chỉ OWNER mới purge được
        if obj.owner_identity_id != command.requester_identity_id:
            raise PermissionDeniedException()

        # Xóa blob của tất cả version trước khi đánh dấu PURGED
        versions = await self._load_version.find_by_object(obj.object_id)
        for version in versions:
            try:
                await self._blob.delete(version.storage_pointer)
            except Exception:
                _log.warning(
                    "Failed to delete blob for version %s — pointer: %s",
                    version.version_id.hex(), version.storage_pointer
                )

        # Xóa blob của object (nếu pointer khác với version hiện tại)
        if obj.storage_pointer:
            try:
                await self._blob.delete(obj.storage_pointer)
            except Exception:
                _log.warning(
                    "Failed to delete blob for object %s — pointer: %s",
                    obj.object_id.hex(), obj.storage_pointer
                )

        # Đánh dấu PURGED trong DB — giữ row để có audit trail
        now = datetime.now(timezone.utc)
        purged = obj.purge(now)
        await self._save.update(purged)
        await self._audit.record(obj.object_id, command.requester_identity_id, "PURGE")
```

> **Lưu ý**: Purge không xóa row khỏi DB — chỉ đổi status thành PURGED. Row cần giữ lại để audit trail hoạt động. Blob storage mới thực sự xóa dữ liệu.

---

### 11.6 Versioning Use Cases

#### CreateVersionUseCase

**`app/application/usecase/version/CreateVersionUseCase.py`**

```python
import hashlib
from dataclasses import dataclass
from app.application.port.outbound.version.LoadVersionPort import LoadVersionPort
from app.application.port.outbound.version.SaveVersionPort import SaveVersionPort
from app.common.util.IdGenerator import generate_id

@dataclass(frozen=True)
class CreateVersionResult:
    version_id: bytes
    version_number: int
    content_hash: str

class CreateVersionUseCase:
    def __init__(
        self,
        load_object_port: LoadObjectPort,
        save_object_port: SaveObjectPort,
        load_version_port: LoadVersionPort,
        save_version_port: SaveVersionPort,
        blob_storage_port: BlobStoragePort,
        authorization_service: AuthorizationService,
        audit_service: AuditService,
    ) -> None:
        self._load = load_object_port
        self._save = save_object_port
        self._load_version = load_version_port
        self._save_version = save_version_port
        self._blob = blob_storage_port
        self._auth = authorization_service
        self._audit = audit_service

    async def execute(self, command: CreateVersionCommand) -> CreateVersionResult:
        obj = await self._load.find_by_id(command.object_id)
        if obj is None:
            raise ObjectNotFoundException(command.object_id)

        if obj.status != ObjectStatus.ACTIVE:
            raise InvalidObjectStateException(obj.status.value, "ACTIVE")

        await self._auth.require_capability(
            command.requester_identity_id, obj, Capability.WRITE
        )

        # Tính hash trước khi upload
        content_hash = hashlib.sha256(command.data).hexdigest()
        content_size = len(command.data)

        # Upload blob trước — ngoài transaction DB
        version_id = generate_id()
        storage_pointer = await self._blob.generate_pointer(
            obj.owner_identity_id, version_id, command.filename
        )
        await self._blob.upload(storage_pointer, command.data, command.content_type)

        # Xác định version_number kế tiếp
        max_version = await self._load_version.find_max_version_number(command.object_id)
        next_version_number = max_version + 1

        now = datetime.now(timezone.utc)
        version = ObjectVersion(
            version_id=version_id,
            object_id=command.object_id,
            version_number=next_version_number,
            storage_pointer=storage_pointer,
            content_hash=content_hash,
            content_size=content_size,
            mime_type=command.content_type,
            created_by=command.requester_identity_id,
            created_at=now,
        )

        # Transaction DB: save version + update object
        try:
            async with self._tx():
                await self._save_version.save(version)
                updated_obj = obj.update_version(version_id, now)
                await self._save.update(updated_obj)
        except Exception:
            # DB fail sau khi đã upload blob → log để cleanup thủ công
            _log.error(
                "DB failed after blob upload — version_id: %s, pointer: %s",
                version_id.hex(), storage_pointer
            )
            raise

        await self._audit.record(command.object_id, command.requester_identity_id, "UPDATE")
        return CreateVersionResult(
            version_id=version_id,
            version_number=next_version_number,
            content_hash=content_hash,
        )
```

#### ListVersionsUseCase

**`app/application/usecase/version/ListVersionsUseCase.py`**

```python
class ListVersionsUseCase:
    def __init__(
        self,
        load_object_port: LoadObjectPort,
        load_version_port: LoadVersionPort,
        authorization_service: AuthorizationService,
    ) -> None:
        self._load = load_object_port
        self._load_version = load_version_port
        self._auth = authorization_service

    async def execute(self, query: ListVersionsQuery) -> list[ObjectVersion]:
        obj = await self._load.find_by_id(query.object_id)
        if obj is None:
            raise ObjectNotFoundException(query.object_id)

        await self._auth.require_capability(
            query.requester_identity_id, obj, Capability.READ
        )

        # find_by_object trả về sorted desc theo version_number (xem repository)
        return await self._load_version.find_by_object(query.object_id)
```

#### GetVersionUseCase

**`app/application/usecase/version/GetVersionUseCase.py`**

```python
class GetVersionUseCase:
    def __init__(
        self,
        load_object_port: LoadObjectPort,
        load_version_port: LoadVersionPort,
        authorization_service: AuthorizationService,
    ) -> None:
        self._load = load_object_port
        self._load_version = load_version_port
        self._auth = authorization_service

    async def execute(self, query: GetVersionQuery) -> ObjectVersion:
        obj = await self._load.find_by_id(query.object_id)
        if obj is None:
            raise ObjectNotFoundException(query.object_id)

        await self._auth.require_capability(
            query.requester_identity_id, obj, Capability.READ
        )

        version = await self._load_version.find_by_id(query.version_id)
        if version is None or version.object_id != query.object_id:
            # Không tìm thấy hoặc version thuộc object khác — trả not found
            raise ObjectNotFoundException(query.version_id)

        return version
```

#### DownloadVersionUseCase

**`app/application/usecase/version/DownloadVersionUseCase.py`**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class DownloadVersionResult:
    data: bytes
    mime_type: str
    content_hash: str
    version_number: int

class DownloadVersionUseCase:
    def __init__(
        self,
        load_object_port: LoadObjectPort,
        load_version_port: LoadVersionPort,
        blob_storage_port: BlobStoragePort,
        authorization_service: AuthorizationService,
        audit_service: AuditService,
    ) -> None:
        self._load = load_object_port
        self._load_version = load_version_port
        self._blob = blob_storage_port
        self._auth = authorization_service
        self._audit = audit_service

    async def execute(self, query: DownloadVersionQuery) -> DownloadVersionResult:
        obj = await self._load.find_by_id(query.object_id)
        if obj is None:
            raise ObjectNotFoundException(query.object_id)

        await self._auth.require_capability(
            query.requester_identity_id, obj, Capability.DOWNLOAD
        )

        version = await self._load_version.find_by_id(query.version_id)
        if version is None or version.object_id != query.object_id:
            raise ObjectNotFoundException(query.version_id)

        data = await self._blob.download(version.storage_pointer)
        await self._audit.record(
            obj.object_id, query.requester_identity_id, "DOWNLOAD_VERSION"
        )

        return DownloadVersionResult(
            data=data,
            mime_type=version.mime_type,
            content_hash=version.content_hash,
            version_number=version.version_number,
        )
```

---

### 11.7 gRPC Extensions

#### Proto — Versioning

**`app/api/grpc/proto/version_service.proto`**

```protobuf
syntax = "proto3";
package data.version;

service VersionService {
  rpc CreateVersion    (CreateVersionRequest)    returns (CreateVersionResponse);
  rpc ListVersions     (ListVersionsRequest)     returns (ListVersionsResponse);
  rpc GetVersion       (GetVersionRequest)       returns (GetVersionResponse);
  rpc DownloadVersion  (DownloadVersionRequest)  returns (DownloadVersionResponse);
}

message CreateVersionRequest {
  string requester_identity_id = 1;
  string object_id             = 2;
  string filename              = 3;
  string content_type          = 4;
  bytes  data                  = 5;
}

message CreateVersionResponse {
  string version_id      = 1;
  int32  version_number  = 2;
  string content_hash    = 3;
}

message ListVersionsRequest {
  string requester_identity_id = 1;
  string object_id             = 2;
}

message VersionInfo {
  string version_id      = 1;
  int32  version_number  = 2;
  string content_hash    = 3;
  int64  content_size    = 4;
  string mime_type       = 5;
  string created_by      = 6;
  string created_at      = 7;
}

message ListVersionsResponse {
  repeated VersionInfo versions = 1;
}

message GetVersionRequest {
  string requester_identity_id = 1;
  string object_id             = 2;
  string version_id            = 3;
}

message GetVersionResponse {
  VersionInfo version = 1;
}

message DownloadVersionRequest {
  string requester_identity_id = 1;
  string object_id             = 2;
  string version_id            = 3;
}

message DownloadVersionResponse {
  bytes  data           = 1;
  string mime_type      = 2;
  string content_hash   = 3;
  int32  version_number = 4;
}
```

#### Proto — Lifecycle extensions cho ObjectService

**Thêm vào `app/api/grpc/proto/object_service.proto`**

```protobuf
service ObjectService {
  // --- existing ---
  rpc CreateObject (CreateObjectRequest) returns (CreateObjectResponse);
  rpc GetObject    (GetObjectRequest)    returns (GetObjectResponse);
  rpc DeleteObject (DeleteObjectRequest) returns (DeleteObjectResponse);
  rpc DownloadObject (DownloadObjectRequest) returns (DownloadObjectResponse);

  // --- phase 11 ---
  rpc ArchiveObject (ArchiveObjectRequest) returns (ArchiveObjectResponse);
  rpc RestoreObject (RestoreObjectRequest) returns (RestoreObjectResponse);
  // PurgeObject chỉ expose qua internal gRPC — không có ở đây
}

message ArchiveObjectRequest {
  string requester_identity_id = 1;
  string object_id             = 2;
}

message ArchiveObjectResponse {
  string object_id = 1;
  string status    = 2;   // "ARCHIVED"
}

message RestoreObjectRequest {
  string requester_identity_id = 1;
  string object_id             = 2;
}

message RestoreObjectResponse {
  string object_id = 1;
  string status    = 2;   // "ACTIVE"
}
```

**Internal proto — Purge**

```protobuf
// app/api/grpc/proto/internal/object_internal_service.proto
service ObjectInternalService {
  rpc PurgeObject (PurgeObjectRequest) returns (PurgeObjectResponse);
}

message PurgeObjectRequest {
  string requester_identity_id = 1;
  string object_id             = 2;
}

message PurgeObjectResponse {
  string object_id = 1;
}
```

#### gRPC Handler — Version

**`app/api/grpc/external/version/VersionGrpcHandler.py`**

```python
import grpc
from app.application.usecase.version.CreateVersionUseCase import CreateVersionUseCase
from app.application.usecase.version.ListVersionsUseCase import ListVersionsUseCase
from app.application.usecase.version.GetVersionUseCase import GetVersionUseCase
from app.application.usecase.version.DownloadVersionUseCase import DownloadVersionUseCase
from app.application.service.authorization.JwtVerificationService import JwtVerificationService
from app.api.grpc.mapper.VersionGrpcMapper import VersionGrpcMapper

class VersionGrpcHandler(VersionServiceServicer):
    def __init__(
        self,
        create_version_use_case: CreateVersionUseCase,
        list_versions_use_case: ListVersionsUseCase,
        get_version_use_case: GetVersionUseCase,
        download_version_use_case: DownloadVersionUseCase,
        jwt_verification_service: JwtVerificationService,
        mapper: VersionGrpcMapper,
    ) -> None:
        self._create = create_version_use_case
        self._list = list_versions_use_case
        self._get = get_version_use_case
        self._download = download_version_use_case
        self._jwt = jwt_verification_service
        self._mapper = mapper

    async def CreateVersion(self, request, context):
        try:
            claims = await self._jwt.verify(self._extract_token(context))
            command = self._mapper.to_create_command(request, claims.identity_id)
            result = await self._create.execute(command)
            return self._mapper.to_create_response(result)
        except PermissionDeniedException:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, "Permission denied")
        except ObjectNotFoundException as e:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
        except InvalidObjectStateException as e:
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(e))
        except Exception:
            await context.abort(grpc.StatusCode.INTERNAL, "Internal error")

    # ListVersions, GetVersion, DownloadVersion — pattern tương tự
```

#### gRPC Handler — Extend ObjectGrpcHandler

Thêm method vào `ObjectGrpcHandler` hiện có:

```python
async def ArchiveObject(self, request, context):
    try:
        claims = await self._jwt.verify(self._extract_token(context))
        command = ArchiveObjectCommand(
            requester_identity_id=claims.identity_id,
            object_id=bytes.fromhex(request.object_id),
        )
        await self._archive_use_case.execute(command)
        return ArchiveObjectResponse(object_id=request.object_id, status="ARCHIVED")
    except InvalidObjectStateException as e:
        await context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(e))
    except PermissionDeniedException:
        await context.abort(grpc.StatusCode.PERMISSION_DENIED, "Permission denied")
    except ObjectNotFoundException as e:
        await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
    except Exception:
        await context.abort(grpc.StatusCode.INTERNAL, "Internal error")

# RestoreObject — pattern tương tự
```

#### gRPC Handler — Purge (Internal)

**`app/api/grpc/internal/object/ObjectInternalGrpcHandler.py`**

```python
class ObjectInternalGrpcHandler(ObjectInternalServiceServicer):
    def __init__(
        self,
        purge_object_use_case: PurgeObjectUseCase,
    ) -> None:
        self._purge = purge_object_use_case

    async def PurgeObject(self, request, context):
        # Internal endpoint — verify service identity qua mTLS (không dùng JWT user)
        try:
            command = PurgeObjectCommand(
                requester_identity_id=bytes.fromhex(request.requester_identity_id),
                object_id=bytes.fromhex(request.object_id),
            )
            await self._purge.execute(command)
            return PurgeObjectResponse(object_id=request.object_id)
        except InvalidObjectStateException as e:
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(e))
        except PermissionDeniedException:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, "Permission denied")
        except ObjectNotFoundException as e:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
        except Exception:
            await context.abort(grpc.StatusCode.INTERNAL, "Internal error")
```

---

### 11.8 Cập nhật DI Configuration

**`app/config/dependency.py`** — thêm binding mới:

```python
from app.application.port.outbound.version.LoadVersionPort import LoadVersionPort
from app.application.port.outbound.version.SaveVersionPort import SaveVersionPort
from app.infrastructure.persistence.repository.version.SqlAlchemyVersionRepository \
    import SqlAlchemyVersionRepository

# Trong dependency.bind({...}):
LoadVersionPort: SqlAlchemyVersionRepository,
SaveVersionPort: SqlAlchemyVersionRepository,
```

Thêm internal handler vào scan:

```python
dependency.scan(
    # ... existing ...
    "app.api.grpc.internal",   # thêm nếu chưa có
)
```

---

### Kiểm tra Phase 11

**Lifecycle:**
- [ ] `ArchiveObjectUseCase`: chỉ `ACTIVE` mới archive được — `SOFT_DELETED` → archive phải fail
- [ ] `RestoreObjectUseCase`: `ARCHIVED` và `SOFT_DELETED` đều restore được → `ACTIVE`
- [ ] `RestoreObjectUseCase`: non-owner gọi restore → `PermissionDeniedException`
- [ ] `PurgeObjectUseCase`: chỉ `SOFT_DELETED` mới purge được — `ACTIVE` → purge phải fail với `InvalidObjectStateException`
- [ ] `PurgeObjectUseCase`: blob bị xóa trước khi DB update — nếu blob fail thì vẫn xóa được (log warning)
- [ ] `PurgeObjectUseCase`: row trong DB vẫn còn sau purge (status = `PURGED`, không xóa row)
- [ ] `DataObject.can_transition_to(PURGED)` trả `False` khi status là `ACTIVE`

**Versioning:**
- [ ] `CreateVersionUseCase`: blob upload trước transaction — nếu DB fail → log với version_id + pointer
- [ ] `CreateVersionUseCase`: `version_number` tăng dần đúng (1, 2, 3, ...) — không có gap hay duplicate
- [ ] `CreateVersionUseCase`: `DataObject.current_version_id` được cập nhật sau khi tạo version mới
- [ ] `GetVersionUseCase`: version thuộc object khác → `ObjectNotFoundException` (không leak thông tin)
- [ ] `DownloadVersionUseCase`: verify `version.object_id == query.object_id` trước khi download
- [ ] `ListVersionsUseCase`: kết quả sorted desc theo `version_number`

**gRPC:**
- [ ] `PurgeObject` chỉ expose qua internal handler — không có trong `ObjectService` public
- [ ] `InvalidObjectStateException` → `FAILED_PRECONDITION` (không phải `INTERNAL`)
- [ ] `VersionGrpcHandler` inject đúng 4 use case + jwt service + mapper

---

## Phase 12 — Advanced: Audit

### 12.1 Audit Service

**`app/application/service/audit/AuditService.py`**

```python
class AuditService:
    def __init__(self, save_audit_port: SaveAuditPort) -> None:
        self._save = save_audit_port

    async def record(
        self, object_id: bytes, actor_id: bytes, action: str
    ) -> None:
        # Không throw exception — audit failure không block operation
        try:
            await self._save.record(object_id, actor_id, action)
        except Exception:
            # Log warning, không raise
            pass
```

### 12.2 Audit Entity & Repository

- `ObjectAuditEntity.py` — SQLAlchemy entity
- `SqlAlchemyAuditRepository.py` — implements `SaveAuditPort`

---

## Phase 13 — Testing

### Unit Tests

| Test | Mục đích |
| --- | --- |
| `test_data_object.py` | DataObject state changes (immutable) |
| `test_object_permission.py` | has_capability() theo role |
| `test_authorization_service.py` | Owner bypass, PUBLIC bypass, ACL deny |
| `test_id_generator.py` | KSUID format (24 bytes, sortable) |
| `test_jwt_verification.py` | Valid token, expired, wrong aud, unknown kid |

### Integration Tests

| Test | Mục đích |
| --- | --- |
| `test_object_repository.py` | Save + find_by_id với real DB |
| `test_permission_repository.py` | ACL CRUD |
| `test_minio_adapter.py` | Upload + download + delete |
| `test_create_object_usecase.py` | End-to-end: upload + metadata + permission |

### Lưu ý Testing

- Unit test: không cần DB, dùng mock port
- Integration test: dùng Docker Compose với PostgreSQL + MinIO thật
- Không mock DB trong integration test (kinh nghiệm từ identity-service: mock/prod divergence gây lỗi migration)

---

## Thứ tự phụ thuộc (Dependency Order)

```
Phase 0 (Môi trường)
  └─ Phase 1 (Domain)
       └─ Phase 2 (Ports)
            ├─ Phase 3 (DB Schema)
            │    └─ Phase 4 (Repositories)
            ├─ Phase 5 (Blob Storage)
            └─ Phase 6 (Authorization Service)
                 └─ Phase 7 (Core Use Cases)
                      └─ Phase 8 (JWT Verification)
                           └─ Phase 9 (API Layer)
                                └─ Phase 10 (Config & Main)
                                     ├─ Phase 11 (Lifecycle & Versioning)
                                     ├─ Phase 12 (Audit)
                                     └─ Phase 13 (Testing)
```

**MVP hoàn chỉnh**: Phase 0 → 10 (có thể bỏ Phase 8 nếu muốn test nội bộ trước).

---

## Ghi chú khi code

1. **Xime Framework**: đọc CLAUDE.md trước khi bind DI
2. **Type hint**: mọi `__init__` param phải có type hint — thiếu → startup fail
3. **Protocol binding**: nếu nhiều class implement cùng Protocol mà không bind tường minh → startup fail
4. **Transaction**: `async with self.transaction():` — không tự manage session
5. **Domain purity**: domain không được import bất cứ thứ gì ngoài standard library + các module domain khác
6. **Blob trước DB**: upload blob trước khi insert DB — nếu DB fail có thể retry; nếu upload fail không insert DB
