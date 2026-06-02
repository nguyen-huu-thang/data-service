from core.transaction.manager import TransactionManager

from app.application.dto.object.DownloadObjectQuery import DownloadObjectQuery
from app.application.dto.object.DownloadObjectResult import DownloadObjectResult
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.storage.BlobStoragePort import BlobStoragePort
from app.application.port.outbound.version.LoadVersionPort import LoadVersionPort
from app.application.service.audit.AuditService import AuditService
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.constants.Capability import Capability
from app.common.constants.ObjectStatus import ObjectStatus
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException


class DownloadObjectUseCase:
    def __init__(
        self,
        transaction: TransactionManager,
        load_object: LoadObjectPort,
        load_version: LoadVersionPort,
        blob_storage: BlobStoragePort,
        authorization_service: AuthorizationService,
        audit_service: AuditService,
    ) -> None:
        self._tx = transaction
        self._load = load_object
        self._load_version = load_version
        self._blob = blob_storage
        self._auth = authorization_service
        self._audit = audit_service

    async def execute(self, query: DownloadObjectQuery) -> DownloadObjectResult:
        storage_pointer: str
        mime_type = "application/octet-stream"

        async with self._tx():
            obj = await self._load.find_by_id(query.object_id)

            if obj is None or obj.status == ObjectStatus.PURGED:
                raise ObjectNotFoundException(query.object_id)

            await self._auth.require_capability(
                query.requester_identity_id,
                obj,
                Capability.DOWNLOAD,
            )

            storage_pointer = obj.storage_pointer

            if obj.current_version_id:
                version = await self._load_version.find_by_id(obj.current_version_id)
                if version:
                    mime_type = version.mime_type

            await self._audit.record(obj.object_id, query.requester_identity_id, "DOWNLOAD")

        # Blob download outside DB transaction — MinIO IO doesn't need a DB session
        data = await self._blob.download(storage_pointer)

        return DownloadObjectResult(
            data=data,
            mime_type=mime_type,
            content_size=len(data),
        )
