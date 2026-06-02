# Quy tắc Code — Domain Patterns

> Các pattern này được rút ra từ code thực tế của identity-service, user-service, trust-service (Java/Spring Boot). Đây là convention của toàn hệ thống Xime — áp dụng khi viết Python cho Data Service.

---

## 1. Immutable State Change

Domain model **không mutate**. Mọi state change return instance mới.

### Java (user-service — nguồn gốc)

```java
public User changeUsername(String newUsername) {
    return new User(id, newUsername, passwordHash, status, createdAt, Instant.now());
}

public UserContact markVerified() {
    return new UserContact(id, userId, type, value, true, isPrimary, createdAt);
}
```

### Python — Data Service áp dụng

```python
from dataclasses import dataclass, replace
from datetime import datetime, timezone

@dataclass(frozen=True)
class DataObject:
    object_id: bytes
    owner_identity_id: bytes
    status: ObjectStatus
    updated_at: datetime

    def archive(self) -> 'DataObject':
        return replace(self, status=ObjectStatus.ARCHIVED, updated_at=_now())

    def soft_delete(self) -> 'DataObject':
        return replace(self, status=ObjectStatus.SOFT_DELETED, updated_at=_now())

def _now() -> datetime:
    return datetime.now(timezone.utc)
```

**Tại sao**: Domain model dễ test (pure function), không có side effect ẩn, không cần mock.

---

## 2. KSUID — ID Generation

Tất cả service trong Xime dùng KSUID (K-Sortable Unique Identifier):

```text
Identity, User Service: 24 bytes = 4 bytes timestamp + 20 bytes random
Trust Service:          20 bytes = 4 bytes timestamp + 16 bytes random
Data Service:           24 bytes (theo identity/user convention)
```

**KSUID epoch**: `1_400_000_000` (Unix time ~ May 2014).

### Python implementation

```python
import os
import struct
import time

KSUID_EPOCH = 1_400_000_000

def generate_id() -> bytes:
    ts = int(time.time()) - KSUID_EPOCH
    return struct.pack('>I', ts) + os.urandom(20)   # 24 bytes total

def id_timestamp(ksuid: bytes) -> int:
    return struct.unpack('>I', ksuid[:4])[0] + KSUID_EPOCH
```

Tính chất:

- **Sortable**: mới hơn = lớn hơn khi so sánh bytes (do timestamp prefix)
- **Unique**: 20 bytes random → collision negligible
- **Opaque**: không encode thông tin nhạy cảm

---

## 3. Identifier Normalization

Bất kỳ value nào dùng để **routing hay lookup** phải normalize trước.

### Java (user-service — nguồn gốc)

```java
public String normalize(String value, IdentifierType type) {
    value = value.strip();
    value = Normalizer.normalize(value, Normalizer.Form.NFKC);
    return switch (type) {
        case EMAIL, USERNAME -> value.toLowerCase();
        case PHONE -> value.replaceAll("[\\s\\-\\(\\)\\+]", "");
    };
}
```

### Python — Data Service áp dụng

```python
import unicodedata

def normalize_identifier(value: str, identifier_type: str) -> str:
    value = value.strip()
    value = unicodedata.normalize('NFKC', value)
    if identifier_type in ('EMAIL', 'USERNAME'):
        return value.lower()
    if identifier_type == 'PHONE':
        return ''.join(c for c in value if c.isdigit())
    return value
```

**Nguyên tắc**: deterministic — `normalize(normalize(x)) == normalize(x)`.

Nếu không normalize → routing sai, duplicate record, security bypass.

---

## 4. Entity ↔ Domain Model Separation

Database entity và domain model là **hai class riêng biệt**. Mapper chuyển đổi giữa hai lớp.

### Java (user-service — pattern)

```java
// ORM Entity — biết về DB
@Entity
@Table(name = "users")
class UserEntity {
    @Id @Column(columnDefinition = "BYTEA") private byte[] id;
    @Column private String username;
    // ... JPA annotations
}

// Domain Model — không biết về DB
class User {
    private final Id id;
    private final String username;
    private final UserStatus status;
    // ... business logic only
}

// Mapper
class UserMapper {
    User toDomain(UserEntity entity) { ... }
    UserEntity toEntity(User domain)  { ... }
}
```

### Python — Data Service áp dụng

```python
# infrastructure/persistence/entity/object/DataObjectEntity.py
# (SQLAlchemy ORM — biết về DB)
class DataObjectEntity(Base):
    __tablename__ = 'data_object'
    object_id: Mapped[bytes] = mapped_column(LargeBinary(24), primary_key=True)
    status: Mapped[str] = mapped_column(String(20))
    # ...

# domain/object/DataObject.py
# (pure Python dataclass — không biết về DB)
@dataclass(frozen=True)
class DataObject:
    object_id: bytes
    status: ObjectStatus
    # ...

# infrastructure/persistence/mapper/DataObjectMapper.py
# (excluded from DI — không scan, gọi trực tiếp)
class DataObjectMapper:
    def to_domain(self, entity: DataObjectEntity) -> DataObject: ...
    def to_entity(self, domain: DataObject) -> DataObjectEntity: ...
```

---

## 5. Port Interface (Protocol) Pattern

Port interface dùng `Protocol`, không phải `ABC`. Không dùng `@abstractmethod`.

```python
# application/port/outbound/object/LoadObjectPort.py
from typing import Protocol
from domain.object.DataObject import DataObject

class LoadObjectPort(Protocol):
    async def find_by_id(self, object_id: bytes) -> DataObject | None: ...
    async def find_by_owner(self, owner_id: bytes) -> list[DataObject]: ...

# application/port/outbound/storage/BlobStoragePort.py
class BlobStoragePort(Protocol):
    async def upload(self, pointer: str, data: bytes) -> None: ...
    async def download(self, pointer: str) -> bytes: ...
    async def delete(self, pointer: str) -> None: ...
```

Bind tường minh trong `config/dependency.py`:

```python
dependency.bind({
    LoadObjectPort: SqlAlchemyObjectRepository,
    SaveObjectPort: SqlAlchemyObjectRepository,
    BlobStoragePort: MinioStorageAdapter,
})
```

---

## 6. gRPC Handler Pattern

Từ `LoginGrpcApi.java` (user-service) — adapted sang Python.

```python
# app/api/grpc/external/object/ObjectGrpcHandler.py
import grpc
from application.usecase.object.CreateObjectUseCase import CreateObjectUseCase
from app.api.grpc.mapper.ObjectGrpcMapper import ObjectGrpcMapper

class ObjectGrpcHandler(object_pb2_grpc.ObjectServiceServicer):
    def __init__(self, create_object_use_case: CreateObjectUseCase,
                 mapper: ObjectGrpcMapper) -> None:
        self._use_case = create_object_use_case
        self._mapper = mapper

    async def CreateObject(self, request, context):
        try:
            command = self._mapper.to_command(request)
            result = await self._use_case.execute(command)
            return self._mapper.to_response(result)
        except PermissionDeniedError as e:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(e))
        except ObjectNotFoundError as e:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
        except Exception as e:
            await context.abort(grpc.StatusCode.INTERNAL, "Internal error")
```

**Quy tắc**:

- Handler chỉ map DTO → Command/Query rồi gọi UseCase
- Exception mapping tại handler — không leak domain exception ra ngoài
- Constructor injection, không dùng decorator hay global

---

## 7. Key Business Logic (từ trust-service)

Pattern cho domain method kiểm tra trạng thái theo thời gian:

```python
# domain/key/KeyContext.py
@dataclass(frozen=True)
class KeyContext:
    key_id: str
    public_key: str
    algorithm: str
    activate_at: datetime
    expires_at: datetime
    is_deleted: bool = False

    def can_sign(self, now: datetime) -> bool:
        return not self.is_deleted and now >= self.activate_at

    def can_verify(self, now: datetime) -> bool:
        return not self.is_deleted and now < self.expires_at

    def is_active(self, now: datetime) -> bool:
        return self.can_verify(now)
```

---

## 8. Tóm tắt — Checklist khi viết Domain Model

- `frozen=True` trên `@dataclass` → immutable
- State change → return `replace(self, field=new_value)`
- Không import gì từ `infrastructure`, `persistence`, `sqlalchemy`
- Domain method nhận `datetime` làm tham số (không gọi `datetime.now()` bên trong) — testable
- ID dùng `bytes` (24 bytes KSUID), không dùng `str` hay `UUID`
- Timestamp dùng `datetime` với `timezone.utc`, không dùng naive datetime
