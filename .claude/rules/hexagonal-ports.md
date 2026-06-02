# Quy tắc Hexagonal Architecture — Đặt Port Interface ở đâu?

## Kết luận áp dụng cho Data Service

**Đặt repository/port interface trong `application/port/outbound/`** — không đặt trong `domain/`.

Lý do: kiến trúc của hệ thống là microservice lớn, nhiều usecase, CQRS-lite, orchestration mạnh ở application layer.

---

## Cách tổ chức đúng

### application/port/outbound/ — định nghĩa "cần gì từ bên ngoài"

```python
# application/port/outbound/object/LoadObjectPort.py
class LoadObjectPort(Protocol):
    async def find_by_id(self, object_id: bytes) -> Optional[DataObject]: ...

# application/port/outbound/object/SaveObjectPort.py
class SaveObjectPort(Protocol):
    async def save(self, obj: DataObject) -> None: ...

# application/port/outbound/storage/BlobStoragePort.py
class BlobStoragePort(Protocol):
    async def upload(self, pointer: str, data: bytes) -> None: ...
    async def download(self, pointer: str) -> bytes: ...
```

### infrastructure/persistence/repository/ — implementation

```python
# infrastructure/persistence/repository/object/SqlAlchemyObjectRepository.py
class SqlAlchemyObjectRepository:
    async def find_by_id(self, object_id: bytes) -> Optional[DataObject]: ...
    async def save(self, obj: DataObject) -> None: ...
```

### config/dependency.py — bind tường minh

```python
dependency.bind({
    LoadObjectPort: SqlAlchemyObjectRepository,
    SaveObjectPort: SqlAlchemyObjectRepository,
    BlobStoragePort: MinioStorageAdapter,
})
```

### domain/ — hoàn toàn sạch

```
domain/
  object/
    DataObject.py       ← entity
    ObjectStatus.py     ← value object / enum
  permission/
    ObjectPermission.py
    Role.py
```

Domain **không biết** gì về DB, cache, repository, query.

---

## Tại sao không đặt trong domain?

Trong DDD kinh điển (Eric Evans), repository đặt trong domain — domain là nơi "thuê" aggregate collection.

Nhưng với kiến trúc của chúng ta:

| Tiêu chí | Repository trong Domain | Repository trong application.port.out |
|---|---|---|
| Domain purity | Kém hơn | Tốt hơn |
| Microservice lớn | Khá ổn | **Tốt hơn** |
| CQRS-lite | Không tối ưu | **Tốt hơn** |
| Tránh God Repository | Dễ bị | **Không bị** |
| Phổ biến hiện nay | Trung bình | **Rất phổ biến** |

---

## Tránh God Repository

Thay vì một `DataObjectRepository` khổng lồ 100 method, tách nhỏ theo usecase:

```python
LoadObjectPort          ← chỉ load
SaveObjectPort          ← chỉ save
CheckObjectExistsPort   ← chỉ check tồn tại
LoadPermissionPort      ← load ACL
```

Rất clean, mỗi port phản ánh đúng một usecase cụ thể.

---

## Áp dụng trong Xime Framework

- Port interface dùng `Protocol` (không phải `ABC`)
- Port nằm trong `port/outbound/` → **excluded** khỏi DI scan tự động
- Implementation nằm trong `infrastructure/` → **scanned** bởi DI
- Bind tường minh trong `config/dependency.py`
- Thiếu binding với nhiều implementation → startup fail ngay
