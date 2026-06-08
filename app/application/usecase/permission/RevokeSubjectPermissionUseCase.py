from xime.core.transaction.manager import TransactionManager

from app.application.dto.permission.RevokeSubjectPermissionCommand import RevokeSubjectPermissionCommand
from app.application.port.outbound.SubjectPermissionRepository import SubjectPermissionRepository


class RevokeSubjectPermissionUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        subject_permission_repository: SubjectPermissionRepository,
    ) -> None:
        self._tx = transaction
        self._repo = subject_permission_repository

    async def execute(self, command: RevokeSubjectPermissionCommand) -> None:
        async with self._tx():
            await self._repo.delete(command.permission_id)
