# Architecture

**English** | [Tiếng Việt](../vn/architecture.md)

---

## Layered Overview

Data Service follows **Hexagonal Architecture** (Ports and Adapters), running on the XIME Framework.

```
External Clients (REST, gRPC)
        ↓
   Adapter Layer (api/)          ← receives requests, maps to commands/queries
        ↓
 Application Layer (application/) ← use cases, authorization, lifecycle logic
        ↓
   Domain Layer (domain/)        ← pure domain model, no framework dependencies
        ↑
Infrastructure Layer (infrastructure/) ← DB repositories, blob storage adapter
        ↑
 Integration Layer (integration/)     ← Identity Service, Trust Service clients
```

The domain layer knows nothing about databases, HTTP, or gRPC. The infrastructure layer knows nothing about use cases. Dependencies always point inward.

---

## Directory Structure

```
app/
├── main.py                              ← single entry point
│
├── api/                                 ← adapter layer
│   ├── grpc/
│   │   ├── external/                    ← gRPC handlers for external clients
│   │   │   ├── object/
│   │   │   ├── permission/
│   │   │   └── version/
│   │   ├── internal/                    ← gRPC handlers for internal services
│   │   │   ├── routing/
│   │   │   └── object/
│   │   └── mapper/
│   └── rest/
│       ├── external/
│       ├── internal/
│       └── mapper/
│
├── application/
│   ├── dto/                             ← Commands and Queries (excluded from DI)
│   │   ├── object/
│   │   │   ├── CreateObjectCommand.py
│   │   │   ├── GetObjectQuery.py
│   │   │   └── UpdateObjectCommand.py
│   │   ├── permission/
│   │   └── version/
│   │
│   ├── port/
│   │   ├── inbound/                     ← input port interfaces (excluded from DI)
│   │   └── outbound/                    ← output port interfaces (excluded from DI)
│   │       ├── object/
│   │       │   ├── LoadObjectPort.py
│   │       │   └── SaveObjectPort.py
│   │       ├── permission/
│   │       ├── version/
│   │       └── storage/
│   │           └── BlobStoragePort.py
│   │
│   ├── usecase/                         ← use case implementations (scanned by DI)
│   │   ├── object/
│   │   │   ├── CreateObjectUseCase.py
│   │   │   ├── GetObjectUseCase.py
│   │   │   ├── DeleteObjectUseCase.py
│   │   │   └── ArchiveObjectUseCase.py
│   │   ├── permission/
│   │   │   ├── GrantPermissionUseCase.py
│   │   │   └── RevokePermissionUseCase.py
│   │   └── version/
│   │       └── CreateVersionUseCase.py
│   │
│   └── service/                         ← application services (scanned by DI)
│       ├── authorization/               ← capability evaluation from ACL
│       ├── routing/                     ← shard routing logic
│       ├── lifecycle/                   ← object lifecycle state machine
│       └── audit/
│
├── domain/                              ← pure domain model (excluded from DI)
│   ├── object/
│   │   ├── DataObject.py
│   │   ├── ObjectVersion.py
│   │   └── ObjectStatus.py
│   ├── permission/
│   │   ├── ObjectPermission.py
│   │   ├── ObjectCapability.py
│   │   └── Role.py
│   └── shard/
│       └── ShardInfo.py
│
├── infrastructure/                      ← implementations (scanned by DI)
│   ├── persistence/
│   │   ├── entity/                      ← SQLAlchemy ORM entities
│   │   ├── mapper/                      ← entity ↔ domain model mappers
│   │   └── repository/                  ← implements outbound ports
│   │       ├── object/
│   │       ├── permission/
│   │       └── version/
│   ├── storage/
│   │   └── local/
│   │       └── LocalDiskStorageAdapter.py  ← implements BlobStoragePort
│   └── event/
│       └── publisher/
│
├── integration/                         ← external service clients
│   ├── identity/                        ← JWT verification, identity resolution
│   └── trust/                           ← JWT public key sync, mTLS setup
│
└── config/
    ├── dependency.py                    ← XIME DI: scan packages + bind interfaces
    ├── routing.py
    └── security.py
```

---

## XIME Framework Integration

Data Service uses the XIME Framework for dependency injection, lifecycle management, and routing. Key patterns:

### Constructor Injection Only

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

No `@inject`, no field injection, no service locator. XIME reads the type hints and wires everything at startup.

### Port Interfaces use Protocol

```python
# application/port/outbound/object/SaveObjectPort.py
from typing import Protocol
from domain.object.DataObject import DataObject

class SaveObjectPort(Protocol):
    async def save(self, obj: DataObject) -> None: ...
```

### Explicit Bindings in config/dependency.py

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

If any binding is missing, a circular dependency exists, or a `Protocol` has no implementation, the app fails immediately at startup with a clear error — before handling a single request.

---

## Domain Layer Rules

The `domain/` package is a strict isolation zone:

- No imports from `infrastructure`, `persistence`, `sqlalchemy`, or any framework
- All domain models are `@dataclass(frozen=True)` — immutable
- State changes return a new instance via `dataclasses.replace()`
- IDs are `bytes` (24-byte KSUID), never `str` or `UUID`
- Timestamps use `datetime` with `timezone.utc`

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

Ports (interfaces) live in `application/port/outbound/` — one port per use case, no god repository:

```
LoadObjectPort          ← find by id
SaveObjectPort          ← save / update
CheckObjectExistsPort   ← existence check
LoadPermissionPort      ← load ACL for an object
BlobStoragePort         ← upload / download / delete binary
```

Adapters (implementations) live in `infrastructure/` and are registered in DI automatically via package scanning.

---

## Request Flow

```
HTTP/gRPC Request
      ↓
  API Handler         → maps request to Command/Query
      ↓
  Use Case            → validates, calls authorization service, calls ports
      ↓
  Repository Port     → resolved to SQLAlchemy implementation via DI
      ↓
  PostgreSQL          → returns domain model via entity mapper
```

Binary blob requests follow a separate path:

```
GET /objects/{id}/download
      ↓
  REST Handler        → extracts identity from JWT
      ↓
  Authorization check → load ACL, evaluate DOWNLOAD capability
      ↓
  LocalDiskStorageAdapter → stream file from disk
```
