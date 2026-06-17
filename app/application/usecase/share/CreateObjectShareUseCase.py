import secrets
from datetime import datetime, timezone

from xime.core.transaction.manager import TransactionManager

from app.application.dto.share.CreateObjectShareCommand import CreateObjectShareCommand
from app.application.dto.share.CreateObjectShareResult import CreateObjectShareResult
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.share.ObjectShareRepository import ObjectShareRepository
from app.application.service.audit.AuditService import AuditService
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.AppException import PublicError
from app.domain.audit.valueobject.AuditAction import AuditAction
from app.domain.object.model.ObjectShare import ObjectShare
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.capability.AclCapability import AclCapability
from app.domain.sharedkernel.factory.IdFactory import IdFactory

# Token entropy in bytes (URL-safe base64 → ~1.3 chars/byte)
_TOKEN_BYTES = 24


class CreateObjectShareUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        load_object: LoadObjectPort,
        share_repository: ObjectShareRepository,
        authorization_service: AuthorizationService,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._load = load_object
        self._share = share_repository
        self._auth = authorization_service
        self._audit = audit_service

    async def execute(self, command: CreateObjectShareCommand) -> CreateObjectShareResult:
        now = datetime.now(timezone.utc)

        async with self._tx():
            obj = await self._load.find_by_id(command.object_id)
            if obj is None or obj.status == ObjectStatus.PURGED:
                raise PublicError("E067000")

            await self._auth.require_capability(
                command.requester_identity_id, obj, AclCapability.SHARE
            )

            token = secrets.token_urlsafe(_TOKEN_BYTES)
            share = ObjectShare(
                share_id=IdFactory.generate(),
                object_id=command.object_id,
                share_token=token,
                expires_at=command.expires_at,
                created_at=now,
            )
            await self._share.save(share)

            await self._audit.record(
                command.object_id,
                command.requester_identity_id,
                command.requester_subject_type,
                command.requester_name,
                AuditAction.SHARE,
            )

            return CreateObjectShareResult(
                share_id=share.share_id,
                share_token=token,
                expires_at=command.expires_at,
            )
