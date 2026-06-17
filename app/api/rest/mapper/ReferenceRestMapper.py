from pydantic import BaseModel

from app.application.dto.reference.CreateObjectReferenceResult import CreateObjectReferenceResult
from app.domain.object.model.ObjectReference import ObjectReference
from app.domain.sharedkernel.service.IdService import IdService


class CreateReferenceRequest(BaseModel):
    application_identity_id: str  # Base62
    application_name: str
    resource_type: str
    resource_id: str


class CreateReferenceResponse(BaseModel):
    reference_id: str


class ReferenceResponse(BaseModel):
    reference_id: str
    object_id: str
    application_identity_id: str
    application_name: str
    resource_type: str
    resource_id: str
    created_at: str


class ReferenceListResponse(BaseModel):
    references: list[ReferenceResponse]


class ReferenceRestMapper:
    def to_create_response(self, result: CreateObjectReferenceResult) -> CreateReferenceResponse:
        return CreateReferenceResponse(reference_id=IdService.to_string(result.reference_id))

    def to_reference_response(self, ref: ObjectReference) -> ReferenceResponse:
        return ReferenceResponse(
            reference_id=IdService.to_string(ref.reference_id),
            object_id=IdService.to_string(ref.object_id),
            application_identity_id=IdService.to_string(ref.application_identity_id),
            application_name=ref.application_name,
            resource_type=ref.resource_type.value,
            resource_id=ref.resource_id,
            created_at=ref.created_at.isoformat(),
        )

    def to_list_response(self, refs: list[ObjectReference]) -> ReferenceListResponse:
        return ReferenceListResponse(references=[self.to_reference_response(r) for r in refs])
