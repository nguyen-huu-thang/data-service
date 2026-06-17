from datetime import datetime

from app.domain.object.valueobject.ContentHash import ContentHash
from app.domain.object.valueobject.MimeType import MimeType
from app.domain.sharedkernel.model.Id import Id
from app.domain.subject.valueobject.SubjectType import SubjectType


class ObjectVersion:

    def __init__(
        self,
        version_id: Id,
        object_id: Id,
        version_number: int,
        storage_pointer: str,
        content_hash: ContentHash,
        content_size: int,
        mime_type: MimeType,
        created_by_identity_id: Id,
        created_by_subject_type: SubjectType,
        created_at: datetime,
    ) -> None:
        # Invariants — a version always has a positive number and non-negative size.
        # Bất biến — version luôn có số thứ tự dương và kích thước không âm.
        if version_id is None:
            raise ValueError("version_id is required")
        if object_id is None:
            raise ValueError("object_id is required")
        if version_number < 1:
            raise ValueError("version_number must be >= 1")
        if content_size < 0:
            raise ValueError("content_size must be >= 0")

        self._version_id = version_id

        self._object_id = object_id

        self._version_number = version_number

        self._storage_pointer = storage_pointer

        self._content_hash = content_hash
        self._content_size = content_size
        self._mime_type = mime_type

        self._created_by_identity_id = created_by_identity_id
        self._created_by_subject_type = created_by_subject_type

        self._created_at = created_at

    @property
    def version_id(self) -> Id:
        return self._version_id

    @property
    def object_id(self) -> Id:
        return self._object_id

    @property
    def version_number(self) -> int:
        return self._version_number

    @property
    def storage_pointer(self) -> str:
        return self._storage_pointer

    @property
    def content_hash(self) -> ContentHash:
        return self._content_hash

    @property
    def content_size(self) -> int:
        return self._content_size

    @property
    def mime_type(self) -> MimeType:
        return self._mime_type

    @property
    def created_by_identity_id(self) -> Id:
        return self._created_by_identity_id

    @property
    def created_by_subject_type(self) -> SubjectType:
        return self._created_by_subject_type

    @property
    def created_at(self) -> datetime:
        return self._created_at

    # =========================
    # Query Methods
    # =========================

    def is_initial(self) -> bool:
        # True for the first version created together with the object.
        # Đúng với version đầu tiên được tạo cùng object.
        return self._version_number == 1