import logging

from app.application.port.outbound.audit.SaveAuditPort import SaveAuditPort

_log = logging.getLogger(__name__)


class AuditService:
    def __init__(self, save_audit_port: SaveAuditPort) -> None:
        self._save = save_audit_port

    async def record(
        self,
        object_id: bytes,
        actor_identity_id: bytes,
        action: str,
    ) -> None:
        # Audit failure must never block the main operation
        try:
            await self._save.record(object_id, actor_identity_id, action)
        except Exception:
            _log.warning(
                "Audit record failed — object=%s actor=%s action=%s",
                object_id.hex(),
                actor_identity_id.hex(),
                action,
            )
