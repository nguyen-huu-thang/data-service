from xime.core.transaction.manager import TransactionManager

from app.application.dto.tag.SetObjectTagsCommand import SetObjectTagsCommand
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.tag.ObjectTagRepository import ObjectTagRepository
from app.application.service.audit.AuditService import AuditService
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.AppException import PublicError
from app.domain.audit.valueobject.AuditAction import AuditAction
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.object.valueobject.ObjectTag import ObjectTag
from app.domain.permission.capability.AclCapability import AclCapability


class SetObjectTagsUseCase:
    """Replace the full tag set of an object (empty list clears all tags)."""

    def __init__(
        self,
        transaction: TransactionManager,
        load_object: LoadObjectPort,
        tag_repository: ObjectTagRepository,
        authorization_service: AuthorizationService,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._load = load_object
        self._tags = tag_repository
        self._auth = authorization_service
        self._audit = audit_service

    async def execute(self, command: SetObjectTagsCommand) -> None:
        async with self._tx():
            obj = await self._load.find_by_id(command.object_id)
            if obj is None or obj.status == ObjectStatus.PURGED:
                raise PublicError("E067000")

            await self._auth.require_capability(
                command.requester_identity_id, obj, AclCapability.WRITE
            )

            # Normalize + de-duplicate while preserving order. Invalid tags
            # (empty/too long) raise ValueError → surfaced as a public 400.
            # Chuẩn hóa + khử trùng lặp, giữ thứ tự. Tag không hợp lệ -> 400 public.
            try:
                tags: list[ObjectTag] = []
                seen: set[str] = set()
                for raw in command.tags:
                    tag = ObjectTag(raw)
                    if tag.value not in seen:
                        seen.add(tag.value)
                        tags.append(tag)
            except ValueError as e:
                raise PublicError("E007001", str(e))

            await self._tags.replace_tags(command.object_id, tags)

            await self._audit.record(
                command.object_id,
                command.requester_identity_id,
                command.requester_subject_type,
                command.requester_name,
                AuditAction.SET_TAGS,
            )
