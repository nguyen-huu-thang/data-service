import logging

from fastapi import File, Header, HTTPException, Response, UploadFile

from xime.adapters.web import get, post

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
from app.common.exception.InvalidObjectStateException import InvalidObjectStateException
from app.common.exception.InvalidTokenException import InvalidTokenException
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.common.exception.PermissionDeniedException import PermissionDeniedException

_log = logging.getLogger(__name__)


def _require_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return authorization[7:]


def _parse_id(hex_id: str, label: str = "ID") -> bytes:
    try:
        return bytes.fromhex(hex_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid {label}: {hex_id}")


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
        mapper: VersionRestMapper,
    ) -> None:
        self._create = create_version_use_case
        self._list = list_versions_use_case
        self._get = get_version_use_case
        self._download = download_version_use_case
        self._jwt = jwt_verification_service
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
        try:
            claims = await self._jwt.verify(_require_token(authorization))
            data = await file.read()
            command = CreateVersionCommand(
                requester_identity_id=claims.identity_id,
                requester_subject_type=claims.subject_type,
                requester_name=claims.name,
                object_id=_parse_id(object_id, "object_id"),
                filename=file.filename or "upload",
                content_type=file.content_type or "application/octet-stream",
                data=data,
            )
            result = await self._create.execute(command)
            return self._mapper.to_create_response(result)
        except HTTPException:
            raise
        except InvalidTokenException as e:
            raise HTTPException(status_code=401, detail=str(e))
        except ObjectNotFoundException:
            raise HTTPException(status_code=404, detail="Object not found")
        except InvalidObjectStateException as e:
            raise HTTPException(status_code=409, detail=str(e))
        except PermissionDeniedException:
            raise HTTPException(status_code=403, detail="Permission denied")
        except Exception:
            _log.exception("Unexpected error in create_version")
            raise HTTPException(status_code=500, detail="Internal server error")

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
        try:
            claims = await self._jwt.verify(_require_token(authorization))
            query = ListVersionsQuery(
                requester_identity_id=claims.identity_id,
                requester_subject_type=claims.subject_type,
                requester_name=claims.name,
                object_id=_parse_id(object_id, "object_id"),
            )
            versions = await self._list.execute(query)
            return self._mapper.to_list_response(versions)
        except HTTPException:
            raise
        except InvalidTokenException as e:
            raise HTTPException(status_code=401, detail=str(e))
        except ObjectNotFoundException:
            raise HTTPException(status_code=404, detail="Object not found")
        except PermissionDeniedException:
            raise HTTPException(status_code=403, detail="Permission denied")
        except Exception:
            _log.exception("Unexpected error in list_versions")
            raise HTTPException(status_code=500, detail="Internal server error")

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
        try:
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
        except HTTPException:
            raise
        except InvalidTokenException as e:
            raise HTTPException(status_code=401, detail=str(e))
        except ObjectNotFoundException:
            raise HTTPException(status_code=404, detail="Object or version not found")
        except PermissionDeniedException:
            raise HTTPException(status_code=403, detail="Permission denied")
        except Exception:
            _log.exception("Unexpected error in get_version")
            raise HTTPException(status_code=500, detail="Internal server error")

    @get(
        "/{object_id}/versions/{version_id}/download",
        summary="Download a specific version",
    )
    async def download_version(
        self,
        object_id: str,
        version_id: str,
        authorization: str | None = Header(default=None),
    ) -> Response:
        try:
            claims = await self._jwt.verify(_require_token(authorization))
            query = DownloadVersionQuery(
                requester_identity_id=claims.identity_id,
                requester_subject_type=claims.subject_type,
                requester_name=claims.name,
                object_id=_parse_id(object_id, "object_id"),
                version_id=_parse_id(version_id, "version_id"),
            )
            result = await self._download.execute(query)
            return Response(
                content=result.data,
                media_type=result.mime_type,
                headers={
                    "Content-Disposition": "attachment",
                    "X-Version-Number": str(result.version_number),
                    "X-Content-Hash": result.content_hash,
                },
            )
        except HTTPException:
            raise
        except InvalidTokenException as e:
            raise HTTPException(status_code=401, detail=str(e))
        except ObjectNotFoundException:
            raise HTTPException(status_code=404, detail="Object or version not found")
        except PermissionDeniedException:
            raise HTTPException(status_code=403, detail="Permission denied")
        except Exception:
            _log.exception("Unexpected error in download_version")
            raise HTTPException(status_code=500, detail="Internal server error")
