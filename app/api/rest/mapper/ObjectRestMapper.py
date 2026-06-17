from pydantic import BaseModel

from app.application.dto.object.CreateObjectResult import CreateObjectResult
from app.domain.audit.model.ObjectAudit import ObjectAudit
from app.domain.object.model.DataObject import DataObject
from app.domain.sharedkernel.model.Id import Id
from app.domain.sharedkernel.service.IdService import IdService


class CreateObjectResponse(BaseModel):
    object_id: str
    shard_id: str
    storage_pointer: str


class ObjectResponse(BaseModel):
    object_id: str
    owner_identity_id: str
    tenant_id: str | None
    shard_id: str
    object_type: str
    visibility: str
    status: str
    created_at: str
    updated_at: str


class ObjectStatusResponse(BaseModel):
    object_id: str
    status: str


class AuditEntryResponse(BaseModel):
    audit_id: str
    object_id: str | None
    actor_identity_id: str
    actor_subject_type: str
    actor_name: str
    action: str
    created_at: str


class AuditListResponse(BaseModel):
    entries: list[AuditEntryResponse]


class ObjectRestMapper:
    def to_create_response(self, result: CreateObjectResult) -> CreateObjectResponse:
        return CreateObjectResponse(
            object_id=IdService.to_string(result.object_id),
            shard_id=result.shard_id,
            storage_pointer=result.storage_pointer,
        )

    def to_object_response(self, obj: DataObject) -> ObjectResponse:
        return ObjectResponse(
            object_id=IdService.to_string(obj.object_id),
            owner_identity_id=IdService.to_string(obj.owner_identity_id),
            tenant_id=obj.tenant_id,
            shard_id=obj.shard_id,
            object_type=obj.object_type.value,
            visibility=obj.visibility.value,
            status=obj.status.value,
            created_at=obj.created_at.isoformat(),
            updated_at=obj.updated_at.isoformat(),
        )

    def to_archive_response(self, object_id: Id) -> ObjectStatusResponse:
        return ObjectStatusResponse(object_id=IdService.to_string(object_id), status="ARCHIVED")

    def to_restore_response(self, object_id: Id) -> ObjectStatusResponse:
        return ObjectStatusResponse(object_id=IdService.to_string(object_id), status="ACTIVE")

    def to_audit_entry_response(self, audit: ObjectAudit) -> AuditEntryResponse:
        return AuditEntryResponse(
            audit_id=IdService.to_string(audit.audit_id),
            object_id=IdService.to_string(audit.object_id) if audit.object_id is not None else None,
            actor_identity_id=IdService.to_string(audit.actor_identity_id),
            actor_subject_type=audit.actor_subject_type,
            actor_name=audit.actor_name,
            action=audit.action.value,
            created_at=audit.created_at.isoformat(),
        )

    def to_audit_list_response(self, audits: list[ObjectAudit]) -> AuditListResponse:
        return AuditListResponse(entries=[self.to_audit_entry_response(a) for a in audits])
