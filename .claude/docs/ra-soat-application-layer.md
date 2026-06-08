# Rà soát Application Layer — Data Service

## Mục tiêu

Tài liệu này liệt kê các thành phần có khả năng còn thiếu hoặc sẽ phát sinh khi Data Service được triển khai thực tế.

Đây không phải danh sách bắt buộc.

Chỉ là danh sách tham khảo để rà soát kiến trúc.

---

## Hiện trạng

Application hiện có:

### Service

* AuditService
* AuthorizationService
* JwtVerificationService

### Use Case

#### Object

* CreateObjectUseCase
* GetObjectUseCase
* DownloadObjectUseCase
* ArchiveObjectUseCase
* RestoreObjectUseCase
* DeleteObjectUseCase
* PurgeObjectUseCase

#### Version

* CreateVersionUseCase
* GetVersionUseCase
* DownloadVersionUseCase
* ListVersionsUseCase

---

## Khu vực có thể còn thiếu

### Object Listing

Hiện tại có:

* GetObjectUseCase

Có thể cần:

* ListObjectsUseCase

Lý do:

Người dùng thường cần xem danh sách object theo:

* owner
* tenant
* tag
* status
* object type

---

### Object Visibility

Domain đã có:

```python
change_visibility()
```

Có thể cần:

* ChangeObjectVisibilityUseCase

Lý do:

Visibility là một phần của domain model nhưng hiện chưa thấy use case tương ứng.

---

### Object Sharing

Database đã có:

* object_share

Domain đã có:

* ObjectShare

Có thể cần:

* CreateShareLinkUseCase
* DeleteShareLinkUseCase
* GetShareLinkUseCase
* DownloadSharedObjectUseCase

Lý do:

ObjectShare hiện chưa thấy được sử dụng bởi application layer.

---

### Object Tag

Database đã có:

* object_tag

Domain đã có:

* ObjectTag

Có thể cần:

* UpdateObjectTagsUseCase
* GetObjectTagsUseCase

Lý do:

Tag thường được quản lý riêng với metadata object.

---

### Object Permission

Database đã có:

* object_permission

Domain đã có:

* ObjectPermission

Thư mục:

```text
application/usecase/permission
```

hiện đang trống.

Có thể cần:

* GrantObjectPermissionUseCase
* RevokeObjectPermissionUseCase
* GetObjectPermissionsUseCase

---

### Subject Permission

Database đã có:

* subject_permission

Domain đã có:

* SubjectPermission

Có thể cần:

* GrantSubjectPermissionUseCase
* RevokeSubjectPermissionUseCase
* GetSubjectPermissionsUseCase

---

### Subject Synchronization

Database đã có:

* subject_info

Domain đã có:

* SubjectInfo

Có thể cần:

* SyncSubjectInfoUseCase

Lý do:

Data Service thường cần đồng bộ thông tin subject từ Identity Service.

---

### Audit Query

Database đã có:

* object_audit

Hiện chỉ thấy AuditService.

Có thể cần:

* GetObjectAuditHistoryUseCase

Lý do:

Audit thường cần được hiển thị trong UI.

---

## Service có thể xuất hiện sau này

### Routing Service

Thư mục hiện có:

```text
application/service/routing
```

Có thể phù hợp cho:

* chọn shard
* chọn storage provider
* xác định storage location

Ví dụ:

* ObjectRoutingService

---

### Lifecycle Service

Thư mục hiện có:

```text
application/service/lifecycle
```

Hiện chưa thấy nhu cầu rõ ràng.

Có thể bỏ trống cho tới khi xuất hiện logic vòng đời object phức tạp.

Ví dụ:

* archive policy
* retention policy
* automatic purge

---

## Query Repository

Hiện repository chủ yếu là CRUD cơ bản.

Khi số lượng use case tăng lên có thể xuất hiện nhu cầu:

* find_by_owner()
* find_by_status()
* find_by_type()
* find_by_object()
* find_by_subject()
* find_by_share_token()

Không cần bổ sung sớm.

Chỉ thêm khi use case thực sự cần.

---

## Kết luận

Kiến trúc hiện tại đã đủ để xây dựng MVP.

Những khu vực có khả năng phát sinh sớm nhất:

1. ListObjectsUseCase
2. ChangeObjectVisibilityUseCase
3. CreateShareLinkUseCase
4. GrantObjectPermissionUseCase
5. GetObjectAuditHistoryUseCase
6. ObjectRoutingService

Các thành phần còn lại có thể bổ sung dần theo nhu cầu thực tế.
