import hashlib
import logging
from datetime import datetime, timezone

from core.transaction.manager import TransactionManager

from app.application.dto.object.CreateObjectCommand import CreateObjectCommand
from app.application.dto.object.CreateObjectResult import CreateObjectResult
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.application.port.outbound.permission.SavePermissionPort import SavePermissionPort
from app.application.port.outbound.storage.BlobStoragePort import BlobStoragePort
from app.application.port.outbound.version.SaveVersionPort import SaveVersionPort
from app.application.service.audit.AuditService import AuditService
from app.application.service.routing.ShardRoutingService import ShardRoutingService
from app.common.constants.ObjectStatus import ObjectStatus
from app.common.constants.Role import Role
from app.common.util.IdGenerator import generate_id
from app.domain.object.DataObject import DataObject
from app.domain.object.ObjectVersion import ObjectVersion
from app.domain.permission.ObjectPermission import ObjectPermission

_log = logging.getLogger(__name__)


class CreateObjectUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        blob_storage: BlobStoragePort,
        save_object: SaveObjectPort,
        save_version: SaveVersionPort,
        save_permission: SavePermissionPort,
        routing_service: ShardRoutingService,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._blob = blob_storage
        self._save_object = save_object
        self._save_version = save_version
        self._save_permission = save_permission
        self._routing = routing_service
        self._audit = audit_service

    async def execute(self, command: CreateObjectCommand) -> CreateObjectResult:
        now = datetime.now(timezone.utc)
        object_id = generate_id()
        version_id = generate_id()
        permission_id = generate_id()

        shard_id = self._routing.compute_shard(command.requester_identity_id)

        pointer = await self._blob.generate_pointer(
            command.requester_identity_id, object_id, command.filename
        )

        # Upload blob BEFORE DB transaction.
        # If DB fails after this, the blob is orphaned.
        # Pointer is deterministic so re-upload on retry is safe.
        await self._blob.upload(pointer, command.data, command.content_type)

        content_hash = hashlib.sha256(command.data).hexdigest()

        try:
            async with self._tx():
                obj = DataObject(
                    object_id=object_id,
                    owner_identity_id=command.requester_identity_id,
                    tenant_id=command.tenant_id,
                    shard_id=shard_id,
                    object_type=command.object_type,
                    visibility=command.visibility,
                    status=ObjectStatus.ACTIVE,
                    storage_provider="MINIO",
                    storage_pointer=pointer,
                    metadata_json={},
                    permission_version=1,
                    created_at=now,
                    updated_at=now,
                    current_version_id=version_id,
                )
                version = ObjectVersion(
                    version_id=version_id,
                    object_id=object_id,
                    version_number=1,
                    storage_pointer=pointer,
                    content_hash=content_hash,
                    content_size=len(command.data),
                    mime_type=command.content_type,
                    created_by=command.requester_identity_id,
                    created_at=now,
                )
                permission = ObjectPermission(
                    permission_id=permission_id,
                    object_id=object_id,
                    subject_identity_id=command.requester_identity_id,
                    role=Role.OWNER,
                    created_at=now,
                )

                await self._save_object.save(obj)
                await self._save_version.save(version)
                await self._save_permission.save(permission)

        except Exception:
            _log.warning(
                "DB failed after blob upload — orphaned blob needs cleanup: "
                "object_id=%s pointer=%s",
                object_id.hex(),
                pointer,
            )
            raise

        return CreateObjectResult(
            object_id=object_id,
            shard_id=shard_id,
            storage_pointer=pointer,
        )
