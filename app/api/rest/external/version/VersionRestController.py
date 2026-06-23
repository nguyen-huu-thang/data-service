from fastapi import File, Header, Request, UploadFile
from fastapi.responses import StreamingResponse

from xime.adapters.web import get, post
from xime.adapters.web.files import stream_object
from xime.starters.storage import StorageService

from app.api.rest._upload_stream import UploadFileStream
from app.api.rest.mapper.VersionRestMapper import (
    CreateVersionResponse,
    VersionListResponse,
    VersionResponse,
    VersionRestMapper,
)
from app.application.dto.version.CreateVersionCommand import CreateVersionCommand
from app.application.dto.version.DownloadVersionQuery import DownloadVersionQuery
from app.application.dto.version.GetVersionQuery import GetVersionQuery
from app.application.dto.version.ListVersionsQuery import ListVersionsQuery
from app.application.service.authorization.JwtVerificationService import JwtVerificationService
from app.application.usecase.version.CreateVersionUseCase import CreateVersionUseCase
from app.application.usecase.version.DownloadVersionUseCase import DownloadVersionUseCase
from app.application.usecase.version.GetVersionUseCase import GetVersionUseCase
from app.application.usecase.version.ListVersionsUseCase import ListVersionsUseCase
from app.common.exception.AppException import PublicError
from app.domain.sharedkernel.model.Id import Id
from app.domain.sharedkernel.service.IdService import IdService

# Business and auth errors raised below propagate to the global AppException
# handler (app/api/rest/error_handler.py), which renders {errorKey, code, message}
# and redacts per channel. No per-endpoint try/except needed.
# Lỗi nghiệp vụ và xác thực ném ra dưới đây propagate tới handler AppException toàn
# cục (app/api/rest/error_handler.py) để render {errorKey, code, message} và che
# theo kênh. Không cần try/except theo từng endpoint.


def _require_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise PublicError("E007002", "Missing or invalid Authorization header")
    return authorization[7:]


def _parse_id(base62_id: str, label: str = "ID") -> Id:
    # IDs cross the external boundary as Base62 strings.
    # ID qua biên ngoài dạng chuỗi Base62.
    try:
        return IdService.from_string(base62_id)
    except ValueError:
        raise PublicError("E007001", f"Invalid {label}: {base62_id}")


class VersionRestController:
    prefix = "/api/v1/objects"
    tags = ["versions"]

    def __init__(
        self,
        create_version_use_case: CreateVersionUseCase,
        list_versions_use_case: ListVersionsUseCase,
        get_version_use_case: GetVersionUseCase,
        download_version_use_case: DownloadVersionUseCase,
        jwt_verification_service: JwtVerificationService,
        storage: StorageService,
        mapper: VersionRestMapper,
    ) -> None:
        self._create = create_version_use_case
        self._list = list_versions_use_case
        self._get = get_version_use_case
        self._download = download_version_use_case
        self._jwt = jwt_verification_service
        self._storage = storage
        self._mapper = mapper

    @post(
        "/{object_id}/versions",
        status_code=201,
        response_model=CreateVersionResponse,
        summary="Upload a new version of an object",
    )
    async def create_version(
        self,
        object_id: str,
        file: UploadFile = File(...),
        authorization: str | None = Header(default=None),
    ) -> CreateVersionResponse:
        claims = await self._jwt.verify(_require_token(authorization))
        # Stream the upload instead of reading it fully into memory.
        # Stream upload thay vì đọc hết vào RAM.
        command = CreateVersionCommand(
            requester_identity_id=claims.identity_id,
            requester_subject_type=claims.subject_type,
            requester_name=claims.name,
            object_id=_parse_id(object_id, "object_id"),
            source=UploadFileStream(file),
        )
        result = await self._create.execute(command)
        return self._mapper.to_create_response(result)

    @get(
        "/{object_id}/versions",
        response_model=VersionListResponse,
        summary="List all versions of an object",
    )
    async def list_versions(
        self,
        object_id: str,
        authorization: str | None = Header(default=None),
    ) -> VersionListResponse:
        claims = await self._jwt.verify(_require_token(authorization))
        query = ListVersionsQuery(
            requester_identity_id=claims.identity_id,
            requester_subject_type=claims.subject_type,
            requester_name=claims.name,
            object_id=_parse_id(object_id, "object_id"),
        )
        versions = await self._list.execute(query)
        return self._mapper.to_list_response(versions)

    @get(
        "/{object_id}/versions/{version_id}",
        response_model=VersionResponse,
        summary="Get metadata of a specific version",
    )
    async def get_version(
        self,
        object_id: str,
        version_id: str,
        authorization: str | None = Header(default=None),
    ) -> VersionResponse:
        claims = await self._jwt.verify(_require_token(authorization))
        query = GetVersionQuery(
            requester_identity_id=claims.identity_id,
            requester_subject_type=claims.subject_type,
            requester_name=claims.name,
            object_id=_parse_id(object_id, "object_id"),
            version_id=_parse_id(version_id, "version_id"),
        )
        version = await self._get.execute(query)
        return self._mapper.to_version_response(version)

    @get(
        "/{object_id}/versions/{version_id}/download",
        summary="Download a specific version",
    )
    async def download_version(
        self,
        object_id: str,
        version_id: str,
        request: Request,
        authorization: str | None = Header(default=None),
    ) -> StreamingResponse:
        claims = await self._jwt.verify(_require_token(authorization))
        query = DownloadVersionQuery(
            requester_identity_id=claims.identity_id,
            requester_subject_type=claims.subject_type,
            requester_name=claims.name,
            object_id=_parse_id(object_id, "object_id"),
            version_id=_parse_id(version_id, "version_id"),
        )
        # Authorize + audit in the use case; stream the resolved blob lazily
        # (HTTP Range, ETag) instead of buffering it in memory.
        # Authz + audit ở usecase; stream blob đã phân giải một cách lười (HTTP
        # Range, ETag) thay vì buffer vào RAM.
        result = await self._download.execute(query)
        filename = result.storage_pointer.rsplit("/", 1)[-1]
        response = await stream_object(
            self._storage,
            result.storage_pointer,
            request=request,
            content_type=result.mime_type,
            filename=filename,
            download=True,
        )
        # Preserve the version metadata headers the previous contract exposed.
        # Giữ các header metadata version mà hợp đồng trước đã phơi ra.
        response.headers["X-Version-Number"] = str(result.version_number)
        response.headers["X-Content-Hash"] = result.content_hash
        return response
