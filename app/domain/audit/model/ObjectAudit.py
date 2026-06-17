from datetime import datetime

from app.domain.audit.valueobject.AuditAction import AuditAction
from app.domain.sharedkernel.model.Id import Id


class ObjectAudit:

    def __init__(
        self,
        audit_id: Id,
        object_id: Id | None,
        actor_identity_id: Id,
        actor_subject_type: str,
        actor_name: str,
        action: AuditAction,
        created_at: datetime,
    ) -> None:
        self._audit_id = audit_id

        self._object_id = object_id

        self._actor_identity_id = actor_identity_id
        self._actor_subject_type = actor_subject_type
        self._actor_name = actor_name

        self._action = action

        self._created_at = created_at

    @property
    def audit_id(self) -> Id:
        return self._audit_id

    @property
    def object_id(self) -> Id | None:
        return self._object_id

    @property
    def actor_identity_id(self) -> Id:
        return self._actor_identity_id

    @property
    def actor_subject_type(self) -> str:
        return self._actor_subject_type

    @property
    def actor_name(self) -> str:
        return self._actor_name

    @property
    def action(self) -> AuditAction:
        return self._action

    @property
    def created_at(self) -> datetime:
        return self._created_at