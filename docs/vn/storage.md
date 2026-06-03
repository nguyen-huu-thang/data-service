# Storage

[English](../en/storage.md) | **Tiếng Việt**

---

## Nguyên tắc thiết kế

Data Service tách **metadata** và **nội dung nhị phân** thành hai kho lưu trữ độc lập:

```
PostgreSQL  ←  metadata (ai, cái gì, khi nào, permission, trạng thái)
Local Disk  ←  nội dung nhị phân (bytes thực tế)
```

Database không bao giờ chứa dữ liệu nhị phân. Nó chỉ lưu `storage_pointer` — đường dẫn tương đối trỏ tới file trên disk.

Sự tách biệt này cho phép:
- Database luôn nhỏ và nhanh bất kể khối lượng file
- Blob storage scale độc lập với metadata
- Thay thế storage backend mà không cần thay đổi business logic
- Áp dụng chiến lược backup độc lập cho từng tầng

---

## storage_pointer

Trường `storage_pointer` trong `data_object` là đường dẫn tương đối bên trong storage root được cấu hình:

```
ab12cd34ef567890/documents/report.pdf
owner-shard-prefix/object-id/original-filename
```

Đường dẫn tuyệt đối được resolve lúc runtime bởi storage adapter:

```
{STORAGE_ROOT} / {storage_pointer}
```

Storage root được cấu hình trong `resources/application.yml`. Không bao giờ lưu trong database.

---

## Local Disk Storage Adapter

Implementation hiện tại lưu blob trên filesystem cục bộ và serve qua FastAPI.

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

Adapter này implement `BlobStoragePort`, nên có thể thay thế bằng backend khác (object storage, distributed FS) chỉ bằng cách cập nhật `config/dependency.py` mà không đụng vào bất kỳ use case nào.

---

## Serve Blob qua FastAPI

Nội dung nhị phân **không được serve tĩnh**. Mỗi request tải xuống đều qua kiểm tra authorization:

```
GET /objects/{object_id}/download
          ↓
    Lấy JWT
          ↓
    Xác minh identity
          ↓
    Load ACL, kiểm tra capability DOWNLOAD
          ↓
    Resolve storage_pointer
          ↓
    Stream file từ disk
```

Điều này đảm bảo rằng ngay cả nội dung `PUBLIC` cũng được serve qua endpoint được kiểm soát, nơi có thể áp dụng rate limiting và audit logging.

---

## Vòng đời Object và Storage

Mỗi trạng thái lifecycle có hành vi storage tương ứng:

| Trạng thái | Blob trên Disk | Metadata trong DB |
|---|---|---|
| `ACTIVE` | Có | Có |
| `ARCHIVED` | Có (có thể chuyển cold storage sau) | Có |
| `SOFT_DELETED` | Có | Có (đánh dấu đã xóa) |
| `PURGED` | Đã xóa | Đã xóa |

Khi object chuyển sang `PURGED`, method `delete()` của storage adapter được gọi để xóa blob khỏi disk trước khi xóa metadata.

---

## Versioning và Storage

Mỗi `object_version` có `storage_pointer` riêng. Khi tải lên version mới, blob của version trước được giữ nguyên tại đường dẫn gốc:

```
ab12cd34/v1/report.pdf    ← blob version 1 (giữ lại)
ab12cd34/v2/report.pdf    ← blob version 2 (hiện tại)
```

Blob của version chỉ bị xóa khi toàn bộ object bị purge hoặc khi kích hoạt version-specific purge.

---

## Layout Storage Theo Shard

Mỗi shard có storage root riêng. Object thuộc các shard khác nhau được lưu trong thư mục hoặc volume riêng:

```
/data/
  ├── shard-01/
  │     └── ab12cd34/...
  ├── shard-02/
  │     └── ef567890/...
```

Điều này phản ánh kiến trúc shared-nothing của database layer và giữ data locality phù hợp với storage locality.

---

## Storage Backend Tương Lai

Interface `BlobStoragePort` được thiết kế không phụ thuộc backend. Các implementation trong tương lai có thể bao gồm:

- Object storage (S3-compatible, MinIO)
- Distributed file system
- Cold archival storage cho object `ARCHIVED`
- CDN integration cho object `PUBLIC`

Chuyển đổi backend chỉ cần một implementation mới của `BlobStoragePort` và cập nhật binding trong `config/dependency.py`.
