from datetime import datetime

from app.domain.subject.valueobject.SubjectType import SubjectType
from app.domain.sharedkernel.model.Id import Id


class SubjectInfo:

    def __init__(
        self,
        identity_id: Id,
        subject_type: SubjectType,
        name: str,
        updated_at: datetime,
    ) -> None:
        self._identity_id = identity_id

        self._subject_type = subject_type

        self._name = name

        self._updated_at = updated_at

    @property
    def identity_id(self) -> Id:
        return self._identity_id

    @property
    def subject_type(self) -> SubjectType:
        return self._subject_type

    @property
    def name(self) -> str:
        return self._name

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def update_name(
        self,
        name: str,
        updated_at: datetime,
    ) -> "SubjectInfo":
        # Immutable state change: return a new instance instead of mutating.
        # Đổi trạng thái bất biến: trả instance mới thay vì sửa tại chỗ.
        return SubjectInfo(
            identity_id=self._identity_id,
            subject_type=self._subject_type,
            name=name,
            updated_at=updated_at,
        )