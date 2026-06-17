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
from app.domain.audit.valueobject.AuditAction import AuditAction
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.exception.AppException import PublicError
from app.domain.sharedkernel.factory.IdFactory import IdFactory
from app.domain.object.model.ObjectVersion import ObjectVersion
from app.domain.object.valueobject.ContentHash import ContentHash
from app.domain.object.valueobject.MimeType import MimeType
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.capability.AclCapability import AclCapability

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
            raise PublicError("E067000")

        # Authorize before validating lifecycle state so unauthorized callers
        # cannot probe whether the object is ACTIVE/ARCHIVED/etc.
        await self._auth.require_capability(
            command.requester_identity_id, obj, AclCapability.WRITE
        )

        if obj.status != ObjectStatus.ACTIVE:
            raise PublicError("E067002")

        content_hash = hashlib.sha256(command.data).hexdigest()
        content_size = len(command.data)
        version_id = IdFactory.generate()

        # Upload blob BEFORE DB transaction — blob is not transactional.
        # The pointer keys on version_id (unique up front), so the upload does
        # not depend on the version number computed later inside the lock.
        storage_pointer = await self._blob.generate_pointer(
            obj.owner_identity_id.to_bytes(), version_id.to_bytes(), command.filename
        )
        await self._blob.upload(storage_pointer, command.data, command.content_type)

        now = datetime.now(timezone.utc)

        try:
            async with self._tx():
                # Lock the parent object row so concurrent version creations are
                # serialized. Without this, two callers could read the same
                # "latest" version and collide on UNIQUE(object_id, version_number).
                locked = await self._load.find_by_id_for_update(command.object_id)
                if locked is None or locked.status == ObjectStatus.PURGED:
                    raise PublicError("E067000")
                if locked.status != ObjectStatus.ACTIVE:
                    raise PublicError("E067002")

                # Determine next version number under the lock.
                latest = await self._load_version.find_latest_by_object(command.object_id)
                next_version_number = (latest.version_number + 1) if latest else 1

                version = ObjectVersion(
                    version_id=version_id,
                    object_id=command.object_id,
                    version_number=next_version_number,
                    storage_pointer=storage_pointer,
                    content_hash=ContentHash(content_hash),
                    content_size=content_size,
                    mime_type=MimeType(command.content_type),
                    created_by_identity_id=command.requester_identity_id,
                    created_by_subject_type=command.requester_subject_type,
                    created_at=now,
                )

                await self._save_version.save(version)
                updated_obj = locked.update_version(version_id, now)  # version_id is Id
                await self._save.update(updated_obj)

                # Audit inside the same transaction — atomic with the version.
                # Ghi audit trong cùng transaction - nguyên tử với version.
                await self._audit.record(
                    command.object_id,
                    command.requester_identity_id,
                    command.requester_subject_type,
                    command.requester_name,
                    AuditAction.UPDATE,
                )
        except PublicError:
            # Business validation errors (object not found / wrong state) propagate
            # without the orphaned-blob log below — they are not infrastructure faults.
            # Lỗi nghiệp vụ (object không tồn tại / sai trạng thái) propagate mà không
            # ghi log orphaned-blob bên dưới - chúng không phải lỗi hạ tầng.
            raise
        except Exception:
            _log.error(
                "DB failed after blob upload — orphaned blob needs cleanup: "
                "version_id=%s pointer=%s",
                version_id.to_bytes().hex(),
                storage_pointer,
            )
            raise

        return CreateVersionResult(
            version_id=version_id,
            version_number=next_version_number,
            content_hash=content_hash,
        )
