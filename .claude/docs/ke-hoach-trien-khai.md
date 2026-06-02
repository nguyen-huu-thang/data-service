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
| Phase 4 | Infrastructure — Repositories | ⬜ Chưa bắt đầu |
| Phase 5 | Infrastructure — Blob Storage | ⬜ Chưa bắt đầu |
| Phase 6 | Application — Authorization | ⬜ Chưa bắt đầu |
| Phase 7 | Application — Core Use Cases | ⬜ Chưa bắt đầu |
| Phase 8 | Security — JWT Verification | ⬜ Chưa bắt đầu |
| Phase 9 | API Layer — gRPC | ⬜ Chưa bắt đầu |
| Phase 10 | Config & Entry Point | ⬜ Chưa bắt đầu |
| Phase 11 | Advanced — Lifecycle & Versioning | ⬜ Chưa bắt đầu |
| Phase 12 | Advanced — Audit | ⬜ Chưa bắt đầu |
| Phase 13 | Testing | ⬜ Chưa bắt đầu |

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

- [ ] Repository không có business logic
- [ ] Mapper tách riêng (không nằm trong repository)
- [ ] Không import domain từ entity (chỉ entity biết về domain qua mapper)

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

- [ ] `generate_pointer()` deterministic — cùng input → cùng output
- [ ] Không lưu binary vào DB (chỉ lưu pointer)
- [ ] Error handling đầy đủ cho minio exceptions

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

- [ ] Owner bypass ACL
- [ ] PUBLIC object bypass READ/DOWNLOAD
- [ ] `PermissionDeniedException` raised khi không có quyền
- [ ] Không có DB logic trong service này — chỉ gọi port

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

- [ ] Authorization check trước khi mọi thao tác
- [ ] Audit ghi sau mỗi thao tác thành công
- [ ] Không có logic DB trong UseCase — chỉ gọi port
- [ ] CreateObject: nếu DB fail sau khi upload blob → log để cleanup sau
- [ ] Transaction scope rõ ràng

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

Sau khi Phase 10 hoạt động ổn định.

### 11.1 Object Lifecycle

**`app/application/usecase/object/ArchiveObjectUseCase.py`**

```
Steps: verify DELETE cap → obj.archive(now) → SaveObjectPort.update()
```

**`app/application/usecase/object/RestoreObjectUseCase.py`**

```
Steps: verify OWNER (chỉ OWNER mới restore) → obj.restore(now) → update
```

**`app/application/usecase/object/PurgeObjectUseCase.py`**

```
Steps: chỉ chạy với status=SOFT_DELETED → xóa blob → xóa metadata
Lưu ý: purge là bất khả nghịch — cần guard nghiêm ngặt
```

### 11.2 Object Versioning

**`app/application/usecase/version/CreateVersionUseCase.py`**

```
Steps:
  1. Verify WRITE cap
  2. Upload blob mới
  3. Create ObjectVersion (version_number = current_max + 1)
  4. Update DataObject.current_version_id
  5. Save version + update object (transaction)
```

**`app/application/usecase/version/ListVersionsUseCase.py`**
**`app/application/usecase/version/GetVersionUseCase.py`**

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
