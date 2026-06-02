# Cây thư mục dự kiến — Data Service

Cấu trúc này dựa trên khuyến nghị của Xime Framework (xem `D:\code\xime\xime framework\.claude\docs\app-entry-point.md`) và tham khảo user-service (Java) để ánh xạ sang Python.

---

## Cây thư mục

```
data-service/
│
├── app/
│   ├── main.py                              ← Entry point duy nhất
│   │
│   ├── api/                                 ← Adapter layer: nhận request
│   │   ├── grpc/
│   │   │   ├── external/                    ← gRPC handler cho external client
│   │   │   │   ├── object/                  ← CRUD object
│   │   │   │   ├── permission/              ← Quản lý permission
│   │   │   │   └── version/                 ← Versioning
│   │   │   ├── internal/                    ← gRPC handler cho internal service
│   │   │   │   ├── routing/                 ← Shard routing metadata
│   │   │   │   └── object/                  ← Internal object lookup
│   │   │   └── mapper/
│   │   └── rest/
│   │       ├── external/
│   │       ├── internal/
│   │       └── mapper/
│   │
│   ├── application/                         ← Application layer
│   │   ├── dto/                             ← DTOs (excluded from DI)
│   │   │   ├── object/
│   │   │   │   ├── CreateObjectCommand.py
│   │   │   │   ├── GetObjectQuery.py
│   │   │   │   └── UpdateObjectCommand.py
│   │   │   ├── permission/
│   │   │   └── version/
│   │   │
│   │   ├── port/
│   │   │   ├── inbound/                     ← Input port interfaces / Protocol (excluded from DI)
│   │   │   └── outbound/                    ← Output port interfaces / Protocol (excluded from DI)
│   │   │       ├── object/
│   │   │       │   ├── LoadObjectPort.py
│   │   │       │   └── SaveObjectPort.py
│   │   │       ├── permission/
│   │   │       ├── version/
│   │   │       └── storage/
│   │   │           └── BlobStoragePort.py   ← Abstraction cho MinIO/S3/filesystem
│   │   │
│   │   ├── usecase/                         ← Use case implementations (scanned by DI)
│   │   │   ├── object/
│   │   │   │   ├── CreateObjectUseCase.py
│   │   │   │   ├── GetObjectUseCase.py
│   │   │   │   ├── DeleteObjectUseCase.py
│   │   │   │   └── ArchiveObjectUseCase.py
│   │   │   ├── permission/
│   │   │   │   ├── GrantPermissionUseCase.py
│   │   │   │   └── RevokePermissionUseCase.py
│   │   │   └── version/
│   │   │       └── CreateVersionUseCase.py
│   │   │
│   │   ├── service/                         ← Application services (scanned by DI)
│   │   │   ├── authorization/               ← Evaluate capability từ ACL
│   │   │   ├── routing/                     ← Shard routing logic
│   │   │   ├── lifecycle/                   ← Object lifecycle state machine
│   │   │   └── audit/
│   │   │
│   │   └── mapper/                          ← Object mappers (excluded from DI)
│   │
│   ├── common/                              ← Shared utilities (excluded from DI)
│   │   ├── constants/
│   │   │   ├── ObjectType.py                ← IMAGE, VIDEO, DOCUMENT, ...
│   │   │   ├── Visibility.py
│   │   │   ├── ObjectStatus.py
│   │   │   └── Capability.py
│   │   ├── exception/
│   │   └── util/
│   │
│   ├── config/                              ← Xime framework configuration
│   │   ├── dependency.py                    ← DI: scan packages + bind interfaces
│   │   ├── routing.py
│   │   └── security.py
│   │
│   ├── domain/                              ← Domain layer (excluded from DI)
│   │   ├── object/
│   │   │   ├── DataObject.py
│   │   │   ├── ObjectVersion.py
│   │   │   └── ObjectStatus.py
│   │   ├── permission/
│   │   │   ├── ObjectPermission.py
│   │   │   ├── ObjectCapability.py
│   │   │   └── Role.py
│   │   └── shard/
│   │       └── ShardInfo.py
│   │
│   ├── integration/                         ← External service clients
│   │   ├── identity/                        ← Verify JWT, resolve identity
│   │   │   ├── client/
│   │   │   ├── contract/
│   │   │   └── resolver/
│   │   └── trust/                           ← mTLS, JWT public key
│   │       ├── key/
│   │       └── certificate/
│   │
│   └── infrastructure/                      ← Infrastructure implementations
│       ├── persistence/                     ← SQLAlchemy repositories
│       │   ├── entity/                      ← ORM entities
│       │   ├── mapper/
│       │   └── repository/                  ← Implements outbound ports (scanned)
│       │       ├── object/
│       │       ├── permission/
│       │       └── version/
│       ├── storage/                         ← Blob storage implementations (scanned)
│       │   ├── minio/
│       │   │   └── MinioStorageAdapter.py   ← Implements BlobStoragePort
│       │   ├── s3/
│       │   └── filesystem/
│       ├── redis/
│       ├── cache/
│       └── event/                           ← Event publishing
│           └── publisher/
│
└── test/
    └── ...
```

---

## Ghi chú

### DI Scanning trong config/dependency.py

```python
dependency.scan(
    "application.usecase",
    "application.service",
    "infrastructure.persistence.repository",
    "infrastructure.storage",
    "infrastructure.redis",
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
    BlobStoragePort: MinioStorageAdapter,   # hoặc S3StorageAdapter
})
```

### Entry point (main.py)

```python
from xime import Application

app = Application()

if __name__ == "__main__":
    app.run()
```

### Chạy ứng dụng

```bash
python app/main.py
```
