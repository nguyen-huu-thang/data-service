from fastapi import File, Form, Header, Request, UploadFile
from fastapi.responses import StreamingResponse

from xime.adapters.web import delete, get, post
from xime.adapters.web.files import stream_object
from xime.starters.storage import StorageService

from app.api.rest._upload_stream import UploadFileStream
from app.api.rest.mapper.ObjectRestMapper import (
    AuditListResponse,
    CreateObjectResponse,
    ObjectResponse,
    ObjectRestMapper,
    ObjectStatusResponse,
)
from app.application.dto.audit.ListObjectAuditQuery import ListObjectAuditQuery
from app.application.dto.object.ArchiveObjectCommand import ArchiveObjectCommand
from app.application.dto.object.CreateObjectCommand import CreateObjectCommand
from app.application.dto.object.DeleteObjectCommand import DeleteObjectCommand
from app.application.dto.object.DownloadObjectQuery import DownloadObjectQuery
from app.application.dto.object.GetObjectQuery import GetObjectQuery
from app.application.dto.object.RestoreObjectCommand import RestoreObjectCommand
from app.application.service.authorization.JwtVerificationService import JwtVerificationService
from app.application.usecase.audit.ListObjectAuditUseCase import ListObjectAuditUseCase
from app.application.usecase.object.ArchiveObjectUseCase import ArchiveObjectUseCase
from app.application.usecase.object.CreateObjectUseCase import CreateObjectUseCase
from app.application.usecase.object.DeleteObjectUseCase import DeleteObjectUseCase
from app.application.usecase.object.DownloadObjectUseCase import DownloadObjectUseCase
from app.application.usecase.object.GetObjectUseCase import GetObjectUseCase
from app.application.usecase.object.RestoreObjectUseCase import RestoreObjectUseCase
from app.common.exception.AppException import PublicError
from app.domain.object.valueobject.ObjectType import ObjectType
from app.domain.object.valueobject.ObjectVisibility import ObjectVisibility
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


def _parse_object_id(base62_id: str) -> Id:
    # Object ids cross the external boundary as Base62 strings.
    # ID qua biên ngoài dạng chuỗi Base62.
    try:
        return IdService.from_string(base62_id)
    except ValueError:
        raise PublicError("E007001", f"Invalid object_id: {base62_id}")


class ObjectRestController:
    prefix = "/api/v1/objects"
    tags = ["objects"]

    def __init__(
        self,
        create_object_use_case: CreateObjectUseCase,
        get_object_use_case: GetObjectUseCase,
        download_object_use_case: DownloadObjectUseCase,
        delete_object_use_case: DeleteObjectUseCase,
        archive_object_use_case: ArchiveObjectUseCase,
        restore_object_use_case: RestoreObjectUseCase,
        list_object_audit_use_case: ListObjectAuditUseCase,
        jwt_verification_service: JwtVerificationService,
        storage: StorageService,
        mapper: ObjectRestMapper,
    ) -> None:
        self._create = create_object_use_case
        self._get = get_object_use_case
        self._download = download_object_use_case
        self._delete = delete_object_use_case
        self._archive = archive_object_use_case
        self._restore = restore_object_use_case
        self._list_audit = list_object_audit_use_case
        self._jwt = jwt_verification_service
        self._storage = storage
        self._mapper = mapper

    @post("", status_code=201, response_model=CreateObjectResponse, summary="Upload a new object")
    async def create_object(
        self,
        object_type: str = Form(...),
        visibility: str = Form(...),
        file: UploadFile = File(...),
        tenant_id: str | None = Form(default=None),
        authorization: str | None = Header(default=None),
    ) -> CreateObjectResponse:
        claims = await self._jwt.verify(_require_token(authorization))
        # Enum parsing — a bad value is client input, surfaced as a public 400.
        # Parse enum — giá trị sai là input của client, trả 400 public.
        try:
            parsed_type = ObjectType(object_type)
            parsed_visibility = ObjectVisibility(visibility)
        except ValueError as e:
            raise PublicError("E007001", str(e))
        # Stream the upload (filename/content_type ride on the source) instead of
        # reading it fully into memory.
        # Stream upload (filename/content_type nằm trên source) thay vì đọc hết RAM.
        command = CreateObjectCommand(
            requester_identity_id=claims.identity_id,
            requester_subject_type=claims.subject_type,
            requester_name=claims.name,
            object_type=parsed_type,
            visibility=parsed_visibility,
            source=UploadFileStream(file),
            tenant_id=tenant_id or None,
        )
        result = await self._create.execute(command)
        return self._mapper.to_create_response(result)

    @get("/{object_id}", response_model=ObjectResponse, summary="Get object metadata")
    async def get_object(
        self,
        object_id: str,
        authorization: str | None = Header(default=None),
    ) -> ObjectResponse:
        claims = await self._jwt.verify(_require_token(authorization))
        query = GetObjectQuery(
            requester_identity_id=claims.identity_id,
            requester_subject_type=claims.subject_type,
            requester_name=claims.name,
            object_id=_parse_object_id(object_id),
        )
        obj = await self._get.execute(query)
        return self._mapper.to_object_response(obj)

    @get("/{object_id}/download", summary="Download object blob")
    async def download_object(
        self,
        object_id: str,
        request: Request,
        authorization: str | None = Header(default=None),
    ) -> StreamingResponse:
        claims = await self._jwt.verify(_require_token(authorization))
        query = DownloadObjectQuery(
            requester_identity_id=claims.identity_id,
            requester_subject_type=claims.subject_type,
            requester_name=claims.name,
            object_id=_parse_object_id(object_id),
        )
        # Authorize + audit happen in the use case; it returns the resolved blob
        # location. The blob is then streamed lazily (HTTP Range, ETag, no full
        # buffering in memory) by the framework helper.
        # Authz + audit ở usecase; nó trả vị trí blob đã phân giải. Blob được stream
        # lười (HTTP Range, ETag, không buffer hết vào RAM) qua helper của framework.
        result = await self._download.execute(query)
        filename = result.storage_pointer.rsplit("/", 1)[-1]
        return await stream_object(
            self._storage,
            result.storage_pointer,
            request=request,
            content_type=result.mime_type,
            filename=filename,
            download=True,
        )

    @delete("/{object_id}", status_code=204, summary="Soft delete an object")
    async def delete_object(
        self,
        object_id: str,
        authorization: str | None = Header(default=None),
    ) -> None:
        claims = await self._jwt.verify(_require_token(authorization))
        command = DeleteObjectCommand(
            requester_identity_id=claims.identity_id,
            requester_subject_type=claims.subject_type,
            requester_name=claims.name,
            object_id=_parse_object_id(object_id),
        )
        await self._delete.execute(command)

    @post("/{object_id}/archive", response_model=ObjectStatusResponse, summary="Archive an object")
    async def archive_object(
        self,
        object_id: str,
        authorization: str | None = Header(default=None),
    ) -> ObjectStatusResponse:
        claims = await self._jwt.verify(_require_token(authorization))
        oid = _parse_object_id(object_id)
        await self._archive.execute(
            ArchiveObjectCommand(
                requester_identity_id=claims.identity_id,
                requester_subject_type=claims.subject_type,
                requester_name=claims.name,
                object_id=oid,
            )
        )
        return self._mapper.to_archive_response(oid)

    @post("/{object_id}/restore", response_model=ObjectStatusResponse, summary="Restore an archived or deleted object")
    async def restore_object(
        self,
        object_id: str,
        authorization: str | None = Header(default=None),
    ) -> ObjectStatusResponse:
        claims = await self._jwt.verify(_require_token(authorization))
        oid = _parse_object_id(object_id)
        await self._restore.execute(
            RestoreObjectCommand(
                requester_identity_id=claims.identity_id,
                requester_subject_type=claims.subject_type,
                requester_name=claims.name,
                object_id=oid,
            )
        )
        return self._mapper.to_restore_response(oid)

    @get("/{object_id}/audit", response_model=AuditListResponse, summary="List the audit trail of an object")
    async def list_object_audit(
        self,
        object_id: str,
        authorization: str | None = Header(default=None),
    ) -> AuditListResponse:
        claims = await self._jwt.verify(_require_token(authorization))
        query = ListObjectAuditQuery(
            requester_identity_id=claims.identity_id,
            requester_subject_type=claims.subject_type,
            requester_name=claims.name,
            object_id=_parse_object_id(object_id),
        )
        audits = await self._list_audit.execute(query)
        return self._mapper.to_audit_list_response(audits)
