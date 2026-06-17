from datetime import datetime

from fastapi import Header

from xime.adapters.web import delete, get, post

from app.api.rest.mapper.ObjectRestMapper import ObjectResponse, ObjectRestMapper
from app.api.rest.mapper.ShareRestMapper import (
    CreateShareRequest,
    CreateShareResponse,
    ShareListResponse,
    ShareRestMapper,
)
from app.application.dto.share.CreateObjectShareCommand import CreateObjectShareCommand
from app.application.dto.share.ListObjectSharesQuery import ListObjectSharesQuery
from app.application.dto.share.ResolveObjectShareQuery import ResolveObjectShareQuery
from app.application.dto.share.RevokeObjectShareCommand import RevokeObjectShareCommand
from app.application.service.authorization.JwtVerificationService import JwtVerificationService
from app.application.usecase.share.CreateObjectShareUseCase import CreateObjectShareUseCase
from app.application.usecase.share.ListObjectSharesUseCase import ListObjectSharesUseCase
from app.application.usecase.share.ResolveObjectShareUseCase import ResolveObjectShareUseCase
from app.application.usecase.share.RevokeObjectShareUseCase import RevokeObjectShareUseCase
from app.common.exception.AppException import PublicError
from app.domain.sharedkernel.model.Id import Id
from app.domain.sharedkernel.service.IdService import IdService


def _require_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise PublicError("E007002", "Missing or invalid Authorization header")
    return authorization[7:]


def _parse_id(base62_id: str, label: str = "id") -> Id:
    try:
        return IdService.from_string(base62_id)
    except ValueError:
        raise PublicError("E007001", f"Invalid {label}: {base62_id}")


def _parse_expires_at(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise PublicError("E007001", f"Invalid expires_at: {value}")


class ShareRestController:
    prefix = "/api/v1"
    tags = ["shares"]

    def __init__(
        self,
        create_share_use_case: CreateObjectShareUseCase,
        list_shares_use_case: ListObjectSharesUseCase,
        revoke_share_use_case: RevokeObjectShareUseCase,
        resolve_share_use_case: ResolveObjectShareUseCase,
        jwt_verification_service: JwtVerificationService,
        mapper: ShareRestMapper,
        object_mapper: ObjectRestMapper,
    ) -> None:
        self._create = create_share_use_case
        self._list = list_shares_use_case
        self._revoke = revoke_share_use_case
        self._resolve = resolve_share_use_case
        self._jwt = jwt_verification_service
        self._mapper = mapper
        self._object_mapper = object_mapper

    @post("/objects/{object_id}/shares", status_code=201, response_model=CreateShareResponse, summary="Create a share link for an object")
    async def create_share(
        self,
        object_id: str,
        body: CreateShareRequest | None = None,
        authorization: str | None = Header(default=None),
    ) -> CreateShareResponse:
        claims = await self._jwt.verify(_require_token(authorization))
        expires_at = _parse_expires_at(body.expires_at if body is not None else None)
        result = await self._create.execute(
            CreateObjectShareCommand(
                requester_identity_id=claims.identity_id,
                requester_subject_type=claims.subject_type,
                requester_name=claims.name,
                object_id=_parse_id(object_id, "object_id"),
                expires_at=expires_at,
            )
        )
        return self._mapper.to_create_response(result)

    @get("/objects/{object_id}/shares", response_model=ShareListResponse, summary="List share links of an object")
    async def list_shares(
        self,
        object_id: str,
        authorization: str | None = Header(default=None),
    ) -> ShareListResponse:
        claims = await self._jwt.verify(_require_token(authorization))
        shares = await self._list.execute(
            ListObjectSharesQuery(
                requester_identity_id=claims.identity_id,
                requester_subject_type=claims.subject_type,
                requester_name=claims.name,
                object_id=_parse_id(object_id, "object_id"),
            )
        )
        return self._mapper.to_list_response(shares)

    @delete("/objects/{object_id}/shares/{share_id}", status_code=204, summary="Revoke a share link")
    async def revoke_share(
        self,
        object_id: str,
        share_id: str,
        authorization: str | None = Header(default=None),
    ) -> None:
        claims = await self._jwt.verify(_require_token(authorization))
        await self._revoke.execute(
            RevokeObjectShareCommand(
                requester_identity_id=claims.identity_id,
                requester_subject_type=claims.subject_type,
                requester_name=claims.name,
                object_id=_parse_id(object_id, "object_id"),
                share_id=_parse_id(share_id, "share_id"),
            )
        )

    @get("/shares/{token}", response_model=ObjectResponse, summary="Resolve a share token to its object (public)")
    async def resolve_share(self, token: str) -> ObjectResponse:
        # No JWT — the opaque token is the authorization.
        obj = await self._resolve.execute(ResolveObjectShareQuery(token=token))
        return self._object_mapper.to_object_response(obj)
