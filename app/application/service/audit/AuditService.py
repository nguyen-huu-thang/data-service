import logging
from datetime import datetime, timezone

from app.application.port.outbound.audit.SaveAuditPort import SaveAuditPort
from app.domain.audit.model.ObjectAudit import ObjectAudit
from app.domain.audit.valueobject.AuditAction import AuditAction
from app.domain.sharedkernel.factory.IdFactory import IdFactory
from app.domain.sharedkernel.model.Id import Id

_log = logging.getLogger(__name__)


class AuditService:
    def __init__(self, save_audit_port: SaveAuditPort) -> None:
        self._save = save_audit_port

    async def record(
        self,
        object_id: Id | None,
        actor_identity_id: Id,
        actor_subject_type: str,
        actor_name: str,
        action: AuditAction,
    ) -> None:
        # Build the audit aggregate in the domain, then persist via the port.
        # object_id is None for subject-level actions.
        # Dựng aggregate audit ở domain rồi lưu qua port. object_id = None với
        # hành động cấp-subject.
        audit = ObjectAudit(
            audit_id=IdFactory.generate(),
            object_id=object_id,
            actor_identity_id=actor_identity_id,
            actor_subject_type=actor_subject_type,
            actor_name=actor_name,
            action=action,
            created_at=datetime.now(timezone.utc),
        )

        # Audit failure must never block the main operation.
        # Lỗi ghi audit không bao giờ được chặn nghiệp vụ chính.
        try:
            await self._save.save(audit)
        except Exception:
            _log.warning(
                "Audit record failed — object=%s actor=%s action=%s",
                object_id.to_bytes().hex() if object_id is not None else "-",
                actor_identity_id.to_bytes().hex(),
                action.value,
            )
