import logging
from datetime import datetime, timezone

from xime.core.transaction.manager import TransactionManager

from app.application.dto.object.CreateObjectCommand import CreateObjectCommand
from app.application.dto.object.CreateObjectResult import CreateObjectResult
from app.application.port.outbound.object.SaveObjectPort import SaveObjectPort
from app.application.port.outbound.permission.SavePermissionPort import SavePermissionPort
from app.application.port.outbound.version.SaveVersionPort import SaveVersionPort
from app.application.service.audit.AuditService import AuditService
from app.application.service.storage.BlobWriter import BlobWriter
from app.application.service.storage.ObjectKeyPolicy import ObjectKeyPolicy
from app.domain.audit.valueobject.AuditAction import AuditAction
from app.application.service.routing.ShardRoutingService import ShardRoutingService
from app.domain.sharedkernel.factory.IdFactory import IdFactory
from app.domain.object.model.DataObject import DataObject
from app.domain.object.model.ObjectVersion import ObjectVersion
from app.domain.object.valueobject.ContentHash import ContentHash
from app.domain.object.valueobject.MimeType import MimeType
from app.domain.object.valueobject.ObjectStatus import ObjectStatus
from app.domain.permission.model.ObjectPermission import ObjectPermission
from app.domain.permission.role.Role import Role

_log = logging.getLogger(__name__)


class CreateObjectUseCase:
    """
    Create a new object and its initial version.

    Business flow:

    1. Generate identifiers
    2. Determine shard placement
    3. Upload blob content
    4. Create object metadata
    5. Create initial version record
    6. Grant OWNER permission
    7. Persist all database records
    8. Write audit record

    Blob content and database metadata are intentionally stored separately.
    """

    def __init__(
        self,
        transaction: TransactionManager,
        blob_writer: BlobWriter,
        key_policy: ObjectKeyPolicy,
        save_object: SaveObjectPort,
        save_version: SaveVersionPort,
        save_permission: SavePermissionPort,
        routing_service: ShardRoutingService,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._blob_writer = blob_writer
        self._key_policy = key_policy
        self._save_object = save_object
        self._save_version = save_version
        self._save_permission = save_permission
        self._routing = routing_service
        self._audit = audit_service

    async def execute(self, command: CreateObjectCommand) -> CreateObjectResult:
        now = datetime.now(timezone.utc)

        # Generate stable identifiers up front so they can be reused
        # across blob storage, metadata records, permissions and retries.
        object_id = IdFactory.generate()
        version_id = IdFactory.generate()
        permission_id = IdFactory.generate()

        # Route object ownership to a shard.
        #
        # Using requester identity keeps objects belonging to the same
        # owner colocated, reducing cross-shard access patterns.
        shard_id = self._routing.compute_shard(
            command.requester_identity_id
        )

        # Generate deterministic storage location.
        #
        # A retry should produce the same pointer so duplicate uploads
        # do not create additional objects in storage.
        pointer = self._key_policy.build(
            command.requester_identity_id,
            object_id,
            command.source.filename,
        )

        # Stream the blob into storage BEFORE the database transaction.
        #
        # Object stores typically cannot participate in database transactions, so
        # the upload happens first. BlobWriter streams the source (no full buffer
        # in memory) and returns the content hash + size computed on the fly. The
        # content hash is kept for integrity, dedup and version comparison.
        #
        # Stream blob vào storage TRƯỚC transaction DB. BlobWriter stream nguồn
        # (không buffer hết vào RAM), trả hash + size tính trên đường đi.
        #
        # Trade-off: storage succeeds but DB fails => orphaned blob to clean up
        # later. Acceptable because the pointer is deterministic and retries are
        # idempotent.
        stored = await self._blob_writer.write(pointer, command.source)
        content_hash = stored.content_hash

        try:
            # Object metadata, version metadata and permissions must
            # be committed atomically.
            async with self._tx():

                # Logical object record.
                #
                # Represents ownership, visibility, status and the
                # currently active version.
                obj = DataObject(
                    object_id=object_id,
                    owner_identity_id=command.requester_identity_id,
                    owner_subject_type=command.requester_subject_type,
                    tenant_id=command.tenant_id,
                    shard_id=shard_id,
                    object_type=command.object_type,
                    visibility=command.visibility,
                    status=ObjectStatus.ACTIVE,
                    storage_provider="LOCAL",
                    storage_pointer=pointer,
                    metadata={},
                    permission_version=1,
                    current_version_id=version_id,
                    created_at=now,
                    updated_at=now,
                )

                # Initial immutable version record.
                #
                # Future updates create additional versions while the
                # object points to the current active version.
                version = ObjectVersion(
                    version_id=version_id,
                    object_id=object_id,
                    version_number=1,
                    storage_pointer=pointer,
                    content_hash=ContentHash(content_hash),
                    content_size=stored.content_size,
                    mime_type=MimeType(command.source.content_type),
                    created_by_identity_id=command.requester_identity_id,
                    created_by_subject_type=command.requester_subject_type,
                    created_at=now,
                )

                # Creator automatically becomes OWNER.
                #
                # This guarantees full control over the newly created
                # object without requiring a separate share operation.
                permission = ObjectPermission(
                    permission_id=permission_id,
                    object_id=object_id,
                    subject_identity_id=command.requester_identity_id,
                    subject_type=command.requester_subject_type,
                    role=Role.OWNER,
                    created_at=now,
                )

                await self._save_object.save(obj)
                await self._save_version.save(version)
                await self._save_permission.save(permission)

                # Audit is written inside the same transaction so the audit
                # trail is atomic with the object it describes.
                # Ghi audit trong cùng transaction để vết audit nguyên tử với object.
                await self._audit.record(
                    object_id,
                    command.requester_identity_id,
                    command.requester_subject_type,
                    command.requester_name,
                    AuditAction.CREATE,
                )

        except Exception:
            # Database transaction failed after blob upload.
            #
            # Blob content now exists without corresponding metadata.
            # Background cleanup or reconciliation should eventually
            # remove these orphaned blobs.
            _log.warning(
                "DB failed after blob upload — orphaned blob needs cleanup: "
                "object_id=%s pointer=%s",
                object_id.to_bytes().hex(),
                pointer,
            )
            raise

        return CreateObjectResult(
            object_id=object_id,
            shard_id=shard_id,
            storage_pointer=pointer,
        )
