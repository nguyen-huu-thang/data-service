from datetime import datetime, timezone

from xime.core.transaction.manager import TransactionManager

from app.application.dto.subject.SyncSubjectInfoCommand import SyncSubjectInfoCommand
from app.application.port.outbound.SubjectInfoRepository import SubjectInfoRepository
from app.domain.subject.model.SubjectInfo import SubjectInfo
from app.domain.subject.valueobject.SubjectType import SubjectType


class SyncSubjectInfoUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        subject_info_repository: SubjectInfoRepository,
    ) -> None:
        self._tx = transaction
        self._repo = subject_info_repository

    async def execute(self, command: SyncSubjectInfoCommand) -> None:
        now = datetime.now(timezone.utc)

        async with self._tx():
            existing = await self._repo.find_by_id(command.identity_id)

            if existing is not None:
                existing.update_name(command.name, now)
                await self._repo.save(existing)
            else:
                subject_info = SubjectInfo(
                    identity_id=command.identity_id,
                    subject_type=SubjectType(command.subject_type),
                    name=command.name,
                    updated_at=now,
                )
                await self._repo.save(subject_info)
