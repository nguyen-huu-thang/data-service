import hashlib
import logging
from datetime import datetime, timezone

from xime.core.transaction.manager import TransactionManager

from app.application.dto.version.CreateVersionCommand import CreateVersionCommand
from app.application.dto.version.CreateVersionResult import CreateVersionResult
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.application.port.outbound.storage.BlobStoragePort import BlobStoragePort
from app.application.port.outbound.version.LoadVersionPort import LoadVersionPort
from app.application.port.outbound.version.SaveVersionPort import SaveVersionPort
from app.application.service.audit.AuditService import AuditService
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.constants.Capability import Capability
from app.common.constants.ObjectStatus import ObjectStatus
from app.common.exception.InvalidObjectStateException import InvalidObjectStateException
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.common.util.IdGenerator import generate_id
from app.domain.object.ObjectVersion import ObjectVersion

_log = logging.getLogger(__name__)


class CreateVersionUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        load_object: LoadObjectPort,
        save_object: SaveObjectPort,
        load_version: LoadVersionPort,
        save_version: SaveVersionPort,
        blob_storage: BlobStoragePort,
        authorization_service: AuthorizationService,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._load = load_object
        self._save = save_object
        self._load_version = load_version
        self._save_version = save_version
        self._blob = blob_storage
        self._auth = authorization_service
        self._audit = audit_service

    async def execute(self, command: CreateVersionCommand) -> CreateVersionResult:
        obj = await self._load.find_by_id(command.object_id)

        if obj is None or obj.status == ObjectStatus.PURGED:
            raise ObjectNotFoundException(command.object_id)

        if obj.status != ObjectStatus.ACTIVE:
            raise InvalidObjectStateException(obj.status.value, ObjectStatus.ACTIVE.value)

        await self._auth.require_capability(
            command.requester_identity_id, obj, Capability.WRITE
        )

        content_hash = hashlib.sha256(command.data).hexdigest()
        content_size = len(command.data)
        version_id = generate_id()

        # Upload blob BEFORE DB transaction — blob is not transactional
        storage_pointer = await self._blob.generate_pointer(
            obj.owner_identity_id, version_id, command.filename
        )
        await self._blob.upload(storage_pointer, command.data, command.content_type)

        # Determine next version number from latest existing version
        latest = await self._load_version.find_latest_by_object(command.object_id)
        next_version_number = (latest.version_number + 1) if latest else 1

        now = datetime.now(timezone.utc)
        version = ObjectVersion(
            version_id=version_id,
            object_id=command.object_id,
            version_number=next_version_number,
            storage_pointer=storage_pointer,
            content_hash=content_hash,
            content_size=content_size,
            mime_type=command.content_type,
            created_by=command.requester_identity_id,
            created_at=now,
        )

        try:
            async with self._tx():
                await self._save_version.save(version)
                updated_obj = obj.update_version(version_id, now)
                await self._save.update(updated_obj)
        except Exception:
            _log.error(
                "DB failed after blob upload — orphaned blob needs cleanup: "
                "version_id=%s pointer=%s",
                version_id.hex(),
                storage_pointer,
            )
            raise

        await self._audit.record(command.object_id, command.requester_identity_id, "UPDATE")

        return CreateVersionResult(
            version_id=version_id,
            version_number=next_version_number,
            content_hash=content_hash,
        )
