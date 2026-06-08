from app.api.grpc.generated.version_service_pb2 import (
    CreateVersionResponse,
    DownloadVersionResponse,
    GetVersionResponse,
    ListVersionsResponse,
    VersionInfo,
)
from app.application.dto.version.CreateVersionCommand import CreateVersionCommand
from app.application.dto.version.CreateVersionResult import CreateVersionResult
from app.application.dto.version.DownloadVersionQuery import DownloadVersionQuery
from app.application.dto.version.DownloadVersionResult import DownloadVersionResult
from app.application.dto.version.GetVersionQuery import GetVersionQuery
from app.application.dto.version.ListVersionsQuery import ListVersionsQuery
from app.domain.object.model.ObjectVersion import ObjectVersion


class VersionGrpcMapper:
    def to_create_command(
        self,
        request,
        requester_identity_id: bytes,
        requester_subject_type: str = "HUMAN",
        requester_name: str = "",
    ) -> CreateVersionCommand:
        return CreateVersionCommand(
            requester_identity_id=requester_identity_id,
            requester_subject_type=requester_subject_type,
            requester_name=requester_name,
            object_id=request.object_id,
            filename=request.filename,
            content_type=request.content_type,
            data=request.data,
        )

    def to_create_response(self, result: CreateVersionResult) -> CreateVersionResponse:
        return CreateVersionResponse(
            version_id=result.version_id,
            version_number=result.version_number,
            content_hash=result.content_hash,
        )

    def to_list_query(
        self,
        request,
        requester_identity_id: bytes,
        requester_subject_type: str = "HUMAN",
        requester_name: str = "",
    ) -> ListVersionsQuery:
        return ListVersionsQuery(
            requester_identity_id=requester_identity_id,
            requester_subject_type=requester_subject_type,
            requester_name=requester_name,
            object_id=request.object_id,
        )

    def to_list_response(self, versions: list[ObjectVersion]) -> ListVersionsResponse:
        return ListVersionsResponse(
            versions=[self._to_version_info(v) for v in versions]
        )

    def to_get_query(
        self,
        request,
        requester_identity_id: bytes,
        requester_subject_type: str = "HUMAN",
        requester_name: str = "",
    ) -> GetVersionQuery:
        return GetVersionQuery(
            requester_identity_id=requester_identity_id,
            requester_subject_type=requester_subject_type,
            requester_name=requester_name,
            object_id=request.object_id,
            version_id=request.version_id,
        )

    def to_get_response(self, version: ObjectVersion) -> GetVersionResponse:
        return GetVersionResponse(version=self._to_version_info(version))

    def to_download_query(
        self,
        request,
        requester_identity_id: bytes,
        requester_subject_type: str = "HUMAN",
        requester_name: str = "",
    ) -> DownloadVersionQuery:
        return DownloadVersionQuery(
            requester_identity_id=requester_identity_id,
            requester_subject_type=requester_subject_type,
            requester_name=requester_name,
            object_id=request.object_id,
            version_id=request.version_id,
        )

    def to_download_response(self, result: DownloadVersionResult) -> DownloadVersionResponse:
        return DownloadVersionResponse(
            data=result.data,
            mime_type=result.mime_type,
            content_hash=result.content_hash,
            version_number=result.version_number,
        )

    @staticmethod
    def _to_version_info(version: ObjectVersion) -> VersionInfo:
        return VersionInfo(
            version_id=version.version_id,
            version_number=version.version_number,
            content_hash=version.content_hash.value,
            content_size=version.content_size,
            mime_type=version.mime_type.value,
            created_by=version.created_by_identity_id,
            created_at_unix=int(version.created_at.timestamp()),
        )
