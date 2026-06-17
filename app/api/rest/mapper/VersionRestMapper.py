from pydantic import BaseModel

from app.application.dto.version.CreateVersionResult import CreateVersionResult
from app.domain.object.model.ObjectVersion import ObjectVersion
from app.domain.sharedkernel.service.IdService import IdService


class CreateVersionResponse(BaseModel):
    version_id: str
    version_number: int
    content_hash: str


class VersionResponse(BaseModel):
    version_id: str
    object_id: str
    version_number: int
    content_hash: str
    content_size: int
    mime_type: str
    created_by: str
    created_at: str


class VersionListResponse(BaseModel):
    versions: list[VersionResponse]


class VersionRestMapper:
    def to_create_response(self, result: CreateVersionResult) -> CreateVersionResponse:
        return CreateVersionResponse(
            version_id=IdService.to_string(result.version_id),
            version_number=result.version_number,
            content_hash=result.content_hash,
        )

    def to_version_response(self, version: ObjectVersion) -> VersionResponse:
        return VersionResponse(
            version_id=IdService.to_string(version.version_id),
            object_id=IdService.to_string(version.object_id),
            version_number=version.version_number,
            content_hash=version.content_hash.value,
            content_size=version.content_size,
            mime_type=version.mime_type.value,
            created_by=IdService.to_string(version.created_by_identity_id),
            created_at=version.created_at.isoformat(),
        )

    def to_list_response(self, versions: list[ObjectVersion]) -> VersionListResponse:
        return VersionListResponse(
            versions=[self.to_version_response(v) for v in versions]
        )
