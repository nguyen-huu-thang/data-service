import logging

from fastapi import File, Form, Header, HTTPException, Response, UploadFile

from xime.adapters.web import delete, get, post

from app.api.rest.mapper.ObjectRestMapper import (
    CreateObjectResponse,
    ObjectResponse,
    ObjectRestMapper,
    ObjectStatusResponse,
)
from app.application.dto.object.ArchiveObjectCommand import ArchiveObjectCommand
from app.application.dto.object.CreateObjectCommand import CreateObjectCommand
from app.application.dto.object.DeleteObjectCommand import DeleteObjectCommand
from app.application.dto.object.DownloadObjectQuery import DownloadObjectQuery
from app.application.dto.object.GetObjectQuery import GetObjectQuery
from app.application.dto.object.RestoreObjectCommand import RestoreObjectCommand
from app.application.service.authorization.JwtVerificationService import JwtVerificationService
from app.application.usecase.object.ArchiveObjectUseCase import ArchiveObjectUseCase
from app.application.usecase.object.CreateObjectUseCase import CreateObjectUseCase
from app.application.usecase.object.DeleteObjectUseCase import DeleteObjectUseCase
from app.application.usecase.object.DownloadObjectUseCase import DownloadObjectUseCase
from app.application.usecase.object.GetObjectUseCase import GetObjectUseCase
from app.application.usecase.object.RestoreObjectUseCase import RestoreObjectUseCase
from app.common.constants.ObjectType import ObjectType
from app.common.constants.Visibility import Visibility
from app.common.exception.InvalidObjectStateException import InvalidObjectStateException
from app.common.exception.InvalidTokenException import InvalidTokenException
from app.common.exception.ObjectAlreadyDeletedException import ObjectAlreadyDeletedException
from app.common.exception.ObjectNotFoundException import ObjectNotFoundException
from app.common.exception.PermissionDeniedException import PermissionDeniedException

_log = logging.getLogger(__name__)


def _require_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return authorization[7:]


def _parse_object_id(hex_id: str) -> bytes:
    try:
        return bytes.fromhex(hex_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid object_id: {hex_id}")


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
        jwt_verification_service: JwtVerificationService,
        mapper: ObjectRestMapper,
    ) -> None:
        self._create = create_object_use_case
        self._get = get_object_use_case
        self._download = download_object_use_case
        self._delete = delete_object_use_case
        self._archive = archive_object_use_case
        self._restore = restore_object_use_case
        self._jwt = jwt_verification_service
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
        try:
            claims = await self._jwt.verify(_require_token(authorization))
            data = await file.read()
            command = CreateObjectCommand(
                requester_identity_id=claims.identity_id,
                object_type=ObjectType(object_type),
                visibility=Visibility(visibility),
                filename=file.filename or "upload",
                content_type=file.content_type or "application/octet-stream",
                data=data,
                tenant_id=tenant_id or None,
            )
            result = await self._create.execute(command)
            return self._mapper.to_create_response(result)
        except HTTPException:
            raise
        except InvalidTokenException as e:
            raise HTTPException(status_code=401, detail=str(e))
        except (ValueError, KeyError) as e:
            raise HTTPException(status_code=400, detail=str(e))
        except PermissionDeniedException:
            raise HTTPException(status_code=403, detail="Permission denied")
        except Exception:
            _log.exception("Unexpected error in create_object")
            raise HTTPException(status_code=500, detail="Internal server error")

    @get("/{object_id}", response_model=ObjectResponse, summary="Get object metadata")
    async def get_object(
        self,
        object_id: str,
        authorization: str | None = Header(default=None),
    ) -> ObjectResponse:
        try:
            claims = await self._jwt.verify(_require_token(authorization))
            query = GetObjectQuery(
                requester_identity_id=claims.identity_id,
                object_id=_parse_object_id(object_id),
            )
            obj = await self._get.execute(query)
            return self._mapper.to_object_response(obj)
        except HTTPException:
            raise
        except InvalidTokenException as e:
            raise HTTPException(status_code=401, detail=str(e))
        except ObjectNotFoundException:
            raise HTTPException(status_code=404, detail="Object not found")
        except PermissionDeniedException:
            raise HTTPException(status_code=403, detail="Permission denied")
        except Exception:
            _log.exception("Unexpected error in get_object")
            raise HTTPException(status_code=500, detail="Internal server error")

    @get("/{object_id}/download", summary="Download object blob")
    async def download_object(
        self,
        object_id: str,
        authorization: str | None = Header(default=None),
    ) -> Response:
        try:
            claims = await self._jwt.verify(_require_token(authorization))
            query = DownloadObjectQuery(
                requester_identity_id=claims.identity_id,
                object_id=_parse_object_id(object_id),
            )
            result = await self._download.execute(query)
            return Response(
                content=result.data,
                media_type=result.mime_type,
                headers={
                    "Content-Length": str(result.content_size),
                    "Content-Disposition": "attachment",
                },
            )
        except HTTPException:
            raise
        except InvalidTokenException as e:
            raise HTTPException(status_code=401, detail=str(e))
        except ObjectNotFoundException:
            raise HTTPException(status_code=404, detail="Object not found")
        except PermissionDeniedException:
            raise HTTPException(status_code=403, detail="Permission denied")
        except Exception:
            _log.exception("Unexpected error in download_object")
            raise HTTPException(status_code=500, detail="Internal server error")

    @delete("/{object_id}", status_code=204, summary="Soft delete an object")
    async def delete_object(
        self,
        object_id: str,
        authorization: str | None = Header(default=None),
    ) -> None:
        try:
            claims = await self._jwt.verify(_require_token(authorization))
            command = DeleteObjectCommand(
                requester_identity_id=claims.identity_id,
                object_id=_parse_object_id(object_id),
            )
            await self._delete.execute(command)
        except HTTPException:
            raise
        except InvalidTokenException as e:
            raise HTTPException(status_code=401, detail=str(e))
        except ObjectNotFoundException:
            raise HTTPException(status_code=404, detail="Object not found")
        except ObjectAlreadyDeletedException:
            raise HTTPException(status_code=409, detail="Object is already deleted")
        except PermissionDeniedException:
            raise HTTPException(status_code=403, detail="Permission denied")
        except Exception:
            _log.exception("Unexpected error in delete_object")
            raise HTTPException(status_code=500, detail="Internal server error")

    @post("/{object_id}/archive", response_model=ObjectStatusResponse, summary="Archive an object")
    async def archive_object(
        self,
        object_id: str,
        authorization: str | None = Header(default=None),
    ) -> ObjectStatusResponse:
        try:
            claims = await self._jwt.verify(_require_token(authorization))
            oid = _parse_object_id(object_id)
            await self._archive.execute(
                ArchiveObjectCommand(requester_identity_id=claims.identity_id, object_id=oid)
            )
            return self._mapper.to_archive_response(oid)
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
            _log.exception("Unexpected error in archive_object")
            raise HTTPException(status_code=500, detail="Internal server error")

    @post("/{object_id}/restore", response_model=ObjectStatusResponse, summary="Restore an archived or deleted object")
    async def restore_object(
        self,
        object_id: str,
        authorization: str | None = Header(default=None),
    ) -> ObjectStatusResponse:
        try:
            claims = await self._jwt.verify(_require_token(authorization))
            oid = _parse_object_id(object_id)
            await self._restore.execute(
                RestoreObjectCommand(requester_identity_id=claims.identity_id, object_id=oid)
            )
            return self._mapper.to_restore_response(oid)
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
            _log.exception("Unexpected error in restore_object")
            raise HTTPException(status_code=500, detail="Internal server error")
