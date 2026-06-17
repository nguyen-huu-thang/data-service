from fastapi import Header

from xime.adapters.web import delete, get, post

from app.api.rest.mapper.ReferenceRestMapper import (
    CreateReferenceRequest,
    CreateReferenceResponse,
    ReferenceListResponse,
    ReferenceRestMapper,
)
from app.application.dto.reference.CreateObjectReferenceCommand import CreateObjectReferenceCommand
from app.application.dto.reference.DeleteObjectReferenceCommand import DeleteObjectReferenceCommand
from app.application.dto.reference.ListObjectReferencesQuery import ListObjectReferencesQuery
from app.application.service.authorization.JwtVerificationService import JwtVerificationService
from app.application.usecase.reference.CreateObjectReferenceUseCase import CreateObjectReferenceUseCase
from app.application.usecase.reference.DeleteObjectReferenceUseCase import DeleteObjectReferenceUseCase
from app.application.usecase.reference.ListObjectReferencesUseCase import ListObjectReferencesUseCase
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


class ReferenceRestController:
    prefix = "/api/v1/objects"
    tags = ["references"]

    def __init__(
        self,
        create_reference_use_case: CreateObjectReferenceUseCase,
        list_references_use_case: ListObjectReferencesUseCase,
        delete_reference_use_case: DeleteObjectReferenceUseCase,
        jwt_verification_service: JwtVerificationService,
        mapper: ReferenceRestMapper,
    ) -> None:
        self._create = create_reference_use_case
        self._list = list_references_use_case
        self._delete = delete_reference_use_case
        self._jwt = jwt_verification_service
        self._mapper = mapper

    @post("/{object_id}/references", status_code=201, response_model=CreateReferenceResponse, summary="Link an object to an application resource")
    async def create_reference(
        self,
        object_id: str,
        body: CreateReferenceRequest,
        authorization: str | None = Header(default=None),
    ) -> CreateReferenceResponse:
        claims = await self._jwt.verify(_require_token(authorization))
        result = await self._create.execute(
            CreateObjectReferenceCommand(
                requester_identity_id=claims.identity_id,
                requester_subject_type=claims.subject_type,
                requester_name=claims.name,
                object_id=_parse_id(object_id, "object_id"),
                application_identity_id=_parse_id(body.application_identity_id, "application_identity_id"),
                application_name=body.application_name,
                resource_type=body.resource_type,
                resource_id=body.resource_id,
            )
        )
        return self._mapper.to_create_response(result)

    @get("/{object_id}/references", response_model=ReferenceListResponse, summary="List references of an object")
    async def list_references(
        self,
        object_id: str,
        authorization: str | None = Header(default=None),
    ) -> ReferenceListResponse:
        claims = await self._jwt.verify(_require_token(authorization))
        refs = await self._list.execute(
            ListObjectReferencesQuery(
                requester_identity_id=claims.identity_id,
                requester_subject_type=claims.subject_type,
                requester_name=claims.name,
                object_id=_parse_id(object_id, "object_id"),
            )
        )
        return self._mapper.to_list_response(refs)

    @delete("/{object_id}/references/{reference_id}", status_code=204, summary="Remove a reference")
    async def delete_reference(
        self,
        object_id: str,
        reference_id: str,
        authorization: str | None = Header(default=None),
    ) -> None:
        claims = await self._jwt.verify(_require_token(authorization))
        await self._delete.execute(
            DeleteObjectReferenceCommand(
                requester_identity_id=claims.identity_id,
                requester_subject_type=claims.subject_type,
                requester_name=claims.name,
                object_id=_parse_id(object_id, "object_id"),
                reference_id=_parse_id(reference_id, "reference_id"),
            )
        )
