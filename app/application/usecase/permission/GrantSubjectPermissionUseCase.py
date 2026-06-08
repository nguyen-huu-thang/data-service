from datetime import datetime, timezone

from xime.core.transaction.manager import TransactionManager

from app.application.dto.permission.GrantSubjectPermissionCommand import GrantSubjectPermissionCommand
from app.application.port.outbound.SubjectPermissionRepository import SubjectPermissionRepository
from app.common.util.IdGenerator import generate_id
from app.domain.permission.model.SubjectPermission import SubjectPermission
from app.domain.subject.valueobject.SubjectType import SubjectType


class GrantSubjectPermissionUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        subject_permission_repository: SubjectPermissionRepository,
    ) -> None:
        self._tx = transaction
        self._repo = subject_permission_repository

    async def execute(self, command: GrantSubjectPermissionCommand) -> None:
        now = datetime.now(timezone.utc)

        async with self._tx():
            permission = SubjectPermission(
                permission_id=generate_id(),
                subject_identity_id=command.target_identity_id,
                subject_type=SubjectType(command.target_subject_type),
                permission=command.capability,
                created_at=now,
                updated_at=now,
            )
            await self._repo.save(permission)
