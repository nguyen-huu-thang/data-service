from datetime import datetime, timezone

from xime.core.transaction.manager import TransactionManager

from app.application.dto.subject.SyncSubjectInfoCommand import SyncSubjectInfoCommand
from app.application.port.outbound.subject.SubjectInfoRepository import SubjectInfoRepository
from app.application.service.audit.AuditService import AuditService
from app.domain.audit.valueobject.AuditAction import AuditAction
from app.domain.subject.model.SubjectInfo import SubjectInfo
from app.domain.subject.valueobject.SubjectType import SubjectType


class SyncSubjectInfoUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        subject_info_repository: SubjectInfoRepository,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._repo = subject_info_repository
        self._audit = audit_service

    async def execute(self, command: SyncSubjectInfoCommand) -> None:
        now = datetime.now(timezone.utc)

        async with self._tx():
            existing = await self._repo.find_by_id(command.identity_id)

            if existing is not None:
                updated = existing.update_name(command.name, now)
                await self._repo.save(updated)
            else:
                subject_info = SubjectInfo(
                    identity_id=command.identity_id,
                    subject_type=SubjectType(command.subject_type),
                    name=command.name,
                    updated_at=now,
                )
                await self._repo.save(subject_info)

            # Subject-level action — the subject syncs its own info (object_id=None).
            # Hành động cấp-subject - subject tự đồng bộ thông tin (object_id=None).
            await self._audit.record(
                None,
                command.identity_id,
                command.subject_type,
                command.name,
                AuditAction.SYNC_SUBJECT,
            )
