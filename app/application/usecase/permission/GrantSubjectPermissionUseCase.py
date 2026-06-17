from datetime import datetime, timezone

from xime.core.transaction.manager import TransactionManager

from app.application.dto.permission.GrantSubjectPermissionCommand import GrantSubjectPermissionCommand
from app.application.port.outbound.permission.SubjectPermissionRepository import SubjectPermissionRepository
from app.application.service.audit.AuditService import AuditService
from app.domain.audit.valueobject.AuditAction import AuditAction
from app.domain.sharedkernel.factory.IdFactory import IdFactory
from app.domain.permission.model.SubjectPermission import SubjectPermission
from app.domain.subject.valueobject.SubjectType import SubjectType


class GrantSubjectPermissionUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        subject_permission_repository: SubjectPermissionRepository,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._repo = subject_permission_repository
        self._audit = audit_service

    async def execute(self, command: GrantSubjectPermissionCommand) -> None:
        now = datetime.now(timezone.utc)

        async with self._tx():
            permission = SubjectPermission(
                permission_id=IdFactory.generate(),
                subject_identity_id=command.target_identity_id,
                subject_type=SubjectType(command.target_subject_type),
                permission=command.capability,
                created_at=now,
                updated_at=now,
            )
            await self._repo.save(permission)

            # Subject-level action — not tied to a specific object (object_id=None).
            # Hành động cấp-subject - không gắn object cụ thể (object_id=None).
            await self._audit.record(
                None,
                command.requester_identity_id,
                command.requester_subject_type,
                command.requester_name,
                AuditAction.GRANT_SUBJECT_PERMISSION,
            )
