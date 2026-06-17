from fastapi import Header

from xime.adapters.web import get, put

from app.api.rest.mapper.TagRestMapper import SetTagsRequest, TagListResponse, TagRestMapper
from app.application.dto.tag.ListObjectTagsQuery import ListObjectTagsQuery
from app.application.dto.tag.SetObjectTagsCommand import SetObjectTagsCommand
from app.application.service.authorization.JwtVerificationService import JwtVerificationService
from app.application.usecase.tag.ListObjectTagsUseCase import ListObjectTagsUseCase
from app.application.usecase.tag.SetObjectTagsUseCase import SetObjectTagsUseCase
from app.common.exception.AppException import PublicError
from app.domain.sharedkernel.model.Id import Id
from app.domain.sharedkernel.service.IdService import IdService


def _require_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise PublicError("E007002", "Missing or invalid Authorization header")
    return authorization[7:]


def _parse_object_id(base62_id: str) -> Id:
    try:
        return IdService.from_string(base62_id)
    except ValueError:
        raise PublicError("E007001", f"Invalid object_id: {base62_id}")


class TagRestController:
    prefix = "/api/v1/objects"
    tags = ["tags"]

    def __init__(
        self,
        set_tags_use_case: SetObjectTagsUseCase,
        list_tags_use_case: ListObjectTagsUseCase,
        jwt_verification_service: JwtVerificationService,
        mapper: TagRestMapper,
    ) -> None:
        self._set = set_tags_use_case
        self._list = list_tags_use_case
        self._jwt = jwt_verification_service
        self._mapper = mapper

    @put("/{object_id}/tags", response_model=TagListResponse, summary="Replace the tag set of an object")
    async def set_tags(
        self,
        object_id: str,
        body: SetTagsRequest,
        authorization: str | None = Header(default=None),
    ) -> TagListResponse:
        claims = await self._jwt.verify(_require_token(authorization))
        oid = _parse_object_id(object_id)
        await self._set.execute(
            SetObjectTagsCommand(
                requester_identity_id=claims.identity_id,
                requester_subject_type=claims.subject_type,
                requester_name=claims.name,
                object_id=oid,
                tags=body.tags,
            )
        )
        tags = await self._list.execute(
            ListObjectTagsQuery(
                requester_identity_id=claims.identity_id,
                requester_subject_type=claims.subject_type,
                requester_name=claims.name,
                object_id=oid,
            )
        )
        return self._mapper.to_list_response(tags)

    @get("/{object_id}/tags", response_model=TagListResponse, summary="List the tags of an object")
    async def list_tags(
        self,
        object_id: str,
        authorization: str | None = Header(default=None),
    ) -> TagListResponse:
        claims = await self._jwt.verify(_require_token(authorization))
        tags = await self._list.execute(
            ListObjectTagsQuery(
                requester_identity_id=claims.identity_id,
                requester_subject_type=claims.subject_type,
                requester_name=claims.name,
                object_id=_parse_object_id(object_id),
            )
        )
        return self._mapper.to_list_response(tags)
