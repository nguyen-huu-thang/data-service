from app.application.dto.version.DownloadVersionQuery import DownloadVersionQuery
from app.application.dto.version.DownloadVersionResult import DownloadVersionResult
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.storage.BlobStoragePort import BlobStoragePort
from app.application.port.outbound.version.LoadVersionPort import LoadVersionPort
from app.application.service.audit.AuditService import AuditService
from app.application.service.authorization.AuthorizationService import AuthorizationService
from app.common.constants.Capability import Capability
from app.common.constants.ObjectStatus import ObjectStatus
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException


class DownloadVersionUseCase:
    def __init__(
        self,
        load_object: LoadObjectPort,
        load_version: LoadVersionPort,
        blob_storage: BlobStoragePort,
        authorization_service: AuthorizationService,
        audit_service: AuditService,
    ) -> None:
        self._load = load_object
        self._load_version = load_version
        self._blob = blob_storage
        self._auth = authorization_service
        self._audit = audit_service

    async def execute(self, query: DownloadVersionQuery) -> DownloadVersionResult:
        obj = await self._load.find_by_id(query.object_id)

        if obj is None or obj.status == ObjectStatus.PURGED:
            raise ObjectNotFoundException(query.object_id)

        await self._auth.require_capability(
            query.requester_identity_id, obj, Capability.DOWNLOAD
        )

        version = await self._load_version.find_by_id(query.version_id)

        if version is None or version.object_id != query.object_id:
            raise ObjectNotFoundException(query.version_id)

        data = await self._blob.download(version.storage_pointer)

        await self._audit.record(
            obj.object_id, query.requester_identity_id, "DOWNLOAD_VERSION"
        )

        return DownloadVersionResult(
            data=data,
            mime_type=version.mime_type,
            content_hash=version.content_hash,
            version_number=version.version_number,
        )
