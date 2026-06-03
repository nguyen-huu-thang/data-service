# Storage

**English** | [Tiếng Việt](../vn/storage.md)

---

## Design Principle

Data Service separates **metadata** and **binary content** into two independent stores:

```
PostgreSQL  ←  metadata (who, what, when, permission, status)
Local Disk  ←  binary content (the actual bytes)
```

The database never contains binary data. It only holds a `storage_pointer` — a relative path that locates the file on disk.

This separation allows:
- Database size to stay small and fast regardless of file volume
- Blob storage to scale independently from metadata
- Storage backend to be replaced without changing business logic
- Backup strategies to be applied independently to each layer

---

## storage_pointer

The `storage_pointer` field in `data_object` is a relative path within the configured storage root:

```
ab12cd34ef567890/documents/report.pdf
owner-shard-prefix/object-id/original-filename
```

The absolute path is resolved at runtime by the storage adapter:

```
{STORAGE_ROOT} / {storage_pointer}
```

The storage root is configured in `resources/application.yml`. It is never stored in the database.

---

## Local Disk Storage Adapter

The current implementation stores blobs on the local filesystem and serves them via FastAPI.

```python
# infrastructure/storage/local/LocalDiskStorageAdapter.py
class LocalDiskStorageAdapter:
    def __init__(self, config: StorageConfig) -> None:
        self._root = Path(config.storage_root)

    async def upload(self, pointer: str, data: bytes) -> None:
        path = self._root / pointer
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    async def download(self, pointer: str) -> bytes:
        path = self._root / pointer
        return path.read_bytes()

    async def delete(self, pointer: str) -> None:
        path = self._root / pointer
        path.unlink(missing_ok=True)
```

This adapter implements `BlobStoragePort`, so it can be replaced with another backend (object storage, distributed FS) by updating `config/dependency.py` without touching any use case.

---

## Blob Serving via FastAPI

Binary content is **not served statically**. Every download request goes through an authorization check:

```
GET /objects/{object_id}/download
          ↓
    Extract JWT
          ↓
    Verify identity
          ↓
    Load ACL, check DOWNLOAD capability
          ↓
    Resolve storage_pointer
          ↓
    Stream file from disk
```

This ensures that even `PUBLIC` content is served through a controlled endpoint where rate limiting and audit logging can be applied.

---

## Object Lifecycle and Storage

Each lifecycle state has a corresponding storage behavior:

| Status | Blob on Disk | Metadata in DB |
|---|---|---|
| `ACTIVE` | Present | Present |
| `ARCHIVED` | Present (may be moved to cold storage later) | Present |
| `SOFT_DELETED` | Present | Present (marked deleted) |
| `PURGED` | Deleted | Deleted |

When an object transitions to `PURGED`, the storage adapter's `delete()` method is called to remove the blob from disk before the metadata record is removed.

---

## Versioning and Storage

Each `object_version` has its own `storage_pointer`. When a new version is uploaded, the previous version's blob is retained at its original path:

```
ab12cd34/v1/report.pdf    ← version 1 blob (retained)
ab12cd34/v2/report.pdf    ← version 2 blob (current)
```

Version blobs are only deleted when the entire object is purged or when a version-specific purge is triggered.

---

## Per-Shard Storage Layout

Each shard has its own storage root. Objects belonging to different shards are stored in separate directories or volumes:

```
/data/
  ├── shard-01/
  │     └── ab12cd34/...
  ├── shard-02/
  │     └── ef567890/...
```

This mirrors the shared-nothing architecture of the database layer and keeps storage locality aligned with data locality.

---

## Future Storage Backends

The `BlobStoragePort` interface is designed to be backend-agnostic. Future implementations may include:

- Object storage (S3-compatible, MinIO)
- Distributed file system
- Cold archival storage for `ARCHIVED` objects
- CDN integration for `PUBLIC` objects

Switching backends requires only a new implementation of `BlobStoragePort` and a binding update in `config/dependency.py`.
