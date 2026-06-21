from xime.core.transaction.manager import TransactionManager

from app.application.dto.permission.RevokeSubjectPermissionCommand import RevokeSubjectPermissionCommand
from app.application.port.outbound.permission.LoadSubjectPermissionPort import LoadSubjectPermissionPort
from app.application.port.outbound.permission.SubjectPermissionRepository import SubjectPermissionRepository
from app.application.service.audit.AuditService import AuditService
from app.common.exception.AppException import PublicError
from app.domain.audit.valueobject.AuditAction import AuditAction
from app.domain.permission.capability.ObjectCapability import ObjectCapability
from app.domain.permission.policy.AccessPolicy import AccessPolicy


class RevokeSubjectPermissionUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        subject_permission_repository: SubjectPermissionRepository,
        load_subject_permission_port: LoadSubjectPermissionPort,
        access_policy: AccessPolicy,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._repo = subject_permission_repository
        self._load_subject_permission = load_subject_permission_port
        self._policy = access_policy
        self._audit = audit_service

    async def execute(self, command: RevokeSubjectPermissionCommand) -> None:
        async with self._tx():
            # Revoking system capabilities is an admin operation: the requester
            # must hold DATA_ADMIN_GRANT (same gate as granting).
            # Thu hồi quyền hệ thống là thao tác admin: requester phải có
            # DATA_ADMIN_GRANT (cùng cổng với cấp quyền).
            requester_permissions = await self._load_subject_permission.find_by_subject(
                command.requester_identity_id
            )
            if not self._policy.has_system_capability(
                requester_permissions, ObjectCapability.DATA_ADMIN_GRANT
            ):
                raise PublicError("E007004")

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
