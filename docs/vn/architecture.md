# Kiến trúc

[English](../en/architecture.md) | **Tiếng Việt**

---

## Tổng quan tầng

Data Service theo **Hexagonal Architecture** (Ports and Adapters), chạy trên XIME Framework.

```
External Client (REST, gRPC)
        ↓
   Adapter Layer (api/)          ← nhận request, map sang command/query
        ↓
 Application Layer (application/) ← use case, authorization, lifecycle logic
        ↓
   Domain Layer (domain/)        ← domain model thuần túy, không phụ thuộc framework
        ↑
Infrastructure Layer (infrastructure/) ← DB repository, blob storage adapter
        ↑
 Integration Layer (integration/)     ← client Identity Service, Trust Service
```

Domain layer không biết gì về database, HTTP hay gRPC. Infrastructure layer không biết gì về use case. Dependency luôn hướng vào trong.

---

## Cây thư mục

```
app/
├── main.py                              ← entry point duy nhất
│
├── api/                                 ← adapter layer
│   ├── grpc/
│   │   ├── external/                    ← gRPC handler cho external client
│   │   │   ├── object/
│   │   │   ├── permission/
│   │   │   └── version/
│   │   ├── internal/                    ← gRPC handler cho internal service
│   │   │   ├── routing/
│   │   │   └── object/
│   │   └── mapper/
│   └── rest/
│       ├── external/
│       ├── internal/
│       └── mapper/
│
├── application/
│   ├── dto/                             ← Command và Query (excluded khỏi DI)
│   │   ├── object/                      ← CreateObjectCommand, GetObjectQuery, ArchiveObjectCommand, ...
│   │   ├── permission/
│   │   ├── subject/
│   │   └── version/
│   │
│   ├── port/
│   │   ├── inbound/                     ← input port interface (excluded khỏi DI)
│   │   └── outbound/                    ← output port interface (excluded khỏi DI)
│   │       ├── object/
│   │       │   ├── LoadObjectPort.py
│   │       │   └── SaveObjectPort.py
│   │       ├── audit/
│   │       │   └── SaveAuditPort.py
│   │       ├── permission/
│   │       ├── storage/
│   │       │   └── BlobStoragePort.py
│   │       ├── trust/                   ← port cho Trust certificate và key (Phase 14)
│   │       │   ├── LoadCertificatePort.py
│   │       │   ├── SaveCertificatePort.py
│   │       │   ├── LoadVerificationKeyPort.py
│   │       │   └── SaveVerificationKeyPort.py
│   │       └── version/
│   │
│   ├── usecase/                         ← use case implementation (scanned bởi DI)
│   │   ├── object/                      ← Create, Get, List, Delete, Archive, Restore, ...
│   │   ├── permission/
│   │   ├── subject/
│   │   └── version/
│   │
│   └── service/                         ← application service (scanned bởi DI)
│       ├── authorization/               ← evaluate capability từ ACL
│       ├── routing/                     ← shard routing logic
│       ├── lifecycle/                   ← state machine vòng đời object
│       └── audit/
│
├── domain/                              ← domain model thuần túy (excluded khỏi DI)
│   ├── object/
│   │   ├── model/                       ← DataObject, ObjectVersion, ObjectShare, ...
│   │   └── valueobject/                 ← ObjectStatus, ObjectType, Visibility, ...
│   ├── permission/
│   │   ├── model/                       ← ObjectPermission, SubjectPermission
│   │   ├── capability/                  ← ObjectCapability, AclCapability
│   │   └── role/                        ← Role
│   ├── audit/                           ← ObjectAudit, AuditAction
│   ├── key/                             ← KeyContext (JWT key domain model)
│   ├── shard/                           ← ShardInfo
│   ├── subject/                         ← SubjectInfo, SubjectType
│   ├── sharedkernel/                    ← Id, IdFactory, IdService
│   └── trust/                           ← Certificate, RootCertificate, VerificationKeyRecord
│
├── infrastructure/                      ← implementation (scanned bởi DI)
│   ├── persistence/
│   │   ├── entity/                      ← SQLAlchemy ORM entity
│   │   ├── mapper/                      ← mapper entity ↔ domain model
│   │   └── repository/                  ← implement outbound port
│   │       ├── audit/
│   │       ├── object/
│   │       ├── permission/
│   │       ├── trust/                   ← TrustCertificateRepository, TrustVerificationKeyRepository
│   │       └── version/
│   ├── storage/
│   │   └── local/
│   │       └── LocalDiskStorageAdapter.py  ← implement BlobStoragePort
│   ├── scheduler/                       ← scheduler infrastructure
│   └── event/
│       └── publisher/
│
├── integration/                         ← client service bên ngoài
│   ├── identity/                        ← xác minh JWT, giải quyết identity
│   └── trust/                           ← Trust Service integration (Phase 14)
│       ├── bootstrap/                   ← đọc bootstrap payload lúc khởi động
│       ├── certificate/                 ← đồng bộ certificate mTLS
│       ├── key/                         ← lấy và cache JWT public key
│       ├── publicca/                    ← quản lý Root CA certificate
│       ├── scheduler/                   ← job định kỳ (cert rotation, key refresh)
│       ├── ssl/                         ← SSL context cho gRPC server
│       └── startup/                     ← orchestration khởi động Trust integration
│
└── config/
    ├── dependency.py                    ← XIME DI: scan package + bind interface
    ├── scheduler.py                     ← cấu hình scheduler
    ├── grpc.py
    └── web.py
```

---

## Tích hợp XIME Framework

Data Service dùng XIME Framework cho dependency injection, lifecycle và routing. Các pattern chính:

### Chỉ Constructor Injection

```python
class CreateObjectUseCase:
    def __init__(
        self,
        save_object_port: SaveObjectPort,
        blob_storage_port: BlobStoragePort,
        authorization_service: AuthorizationService,
    ) -> None:
        self._save = save_object_port
        self._storage = blob_storage_port
        self._auth = authorization_service
```

Không `@inject`, không field injection, không service locator. XIME đọc type hint và kết nối mọi thứ lúc startup.

### Port Interface dùng Protocol

```python
# application/port/outbound/object/SaveObjectPort.py
from typing import Protocol
from domain.object.DataObject import DataObject

class SaveObjectPort(Protocol):
    async def save(self, obj: DataObject) -> None: ...
```

### Binding tường minh trong config/dependency.py

```python
from xime import BindingConfig
from application.port.outbound.storage.BlobStoragePort import BlobStoragePort
from infrastructure.storage.local.LocalDiskStorageAdapter import LocalDiskStorageAdapter

dependency = BindingConfig()

dependency.scan(
    "application.usecase",
    "application.service",
    "infrastructure.persistence.repository",
    "infrastructure.storage",
    "infrastructure.event",
    "integration.identity.client",
    "integration.trust",
)

dependency.exclude(
    "domain",
    "dto",
    "entity",
    "port",
    "mapper",
    "constants",
    "exception",
)

dependency.bind({
    BlobStoragePort: LocalDiskStorageAdapter,
})
```

### Fail Fast

Nếu thiếu binding, tồn tại circular dependency hoặc `Protocol` không có implementation, app thất bại ngay lúc startup với thông báo rõ ràng — trước khi xử lý bất kỳ request nào.

---

## Quy tắc Domain Layer

Package `domain/` là vùng cách ly nghiêm ngặt:

- Không import từ `infrastructure`, `persistence`, `sqlalchemy` hay bất kỳ framework nào
- Tất cả domain model dùng `@dataclass(frozen=True)` — bất biến
- Thay đổi trạng thái → trả về instance mới qua `dataclasses.replace()`
- ID dùng `bytes` (24-byte KSUID), không dùng `str` hay `UUID`
- Timestamp dùng `datetime` với `timezone.utc`

```python
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
```

---

## Port / Adapter Pattern

Port (interface) nằm trong `application/port/outbound/` — một port per use case, không có god repository:

```
LoadObjectPort          ← tìm theo id
SaveObjectPort          ← lưu / cập nhật
CheckObjectExistsPort   ← kiểm tra tồn tại
LoadPermissionPort      ← load ACL của object
BlobStoragePort         ← upload / download / delete binary
```

Adapter (implementation) nằm trong `infrastructure/` và được đăng ký vào DI tự động qua package scanning.

---

## Luồng Request

```
HTTP/gRPC Request
      ↓
  API Handler         → map request thành Command/Query
      ↓
  Use Case            → validate, gọi authorization service, gọi port
      ↓
  Repository Port     → được resolve thành SQLAlchemy implementation qua DI
      ↓
  PostgreSQL          → trả về domain model qua entity mapper
```

Request tải blob đi theo đường riêng:

```
GET /objects/{id}/download
      ↓
  REST Handler        → lấy identity từ JWT
      ↓
  Kiểm tra auth       → load ACL, evaluate capability DOWNLOAD
      ↓
  LocalDiskStorageAdapter → stream file từ disk
```
