from xime.core.transaction.manager import TransactionManager

from app.application.dto.permission.RevokeSubjectPermissionCommand import RevokeSubjectPermissionCommand
from app.application.port.outbound.permission.SubjectPermissionRepository import SubjectPermissionRepository
from app.application.service.audit.AuditService import AuditService
from app.domain.audit.valueobject.AuditAction import AuditAction


class RevokeSubjectPermissionUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        subject_permission_repository: SubjectPermissionRepository,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._repo = subject_permission_repository
        self._audit = audit_service

    async def execute(self, command: RevokeSubjectPermissionCommand) -> None:
        async with self._tx():
            await self._repo.delete(command.permission_id)

            # Subject-level action — not tied to a specific object (object_id=None).
            # Hành động cấp-subject - không gắn object cụ thể (object_id=None).
            await self._audit.record(
                None,
                command.requester_identity_id,
                command.requester_subject_type,
                command.requester_name,
                AuditAction.REVOKE_SUBJECT_PERMISSION,
            )
