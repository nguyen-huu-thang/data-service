from dataclasses import dataclass

from app.application.dto.upload.UploadStream import UploadStream
from app.domain.sharedkernel.model.Id import Id

from app.domain.object.valueobject.ObjectType import ObjectType
from app.domain.object.valueobject.ObjectVisibility import ObjectVisibility


@dataclass(frozen=True)
class CreateObjectCommand:
    requester_identity_id: Id
    requester_subject_type: str
    requester_name: str
    object_type: ObjectType
    visibility: ObjectVisibility
    # Streaming source of the blob (filename + content_type live on it). Consumed
    # once by the use case; not buffered in memory.
    # Nguồn stream của blob (filename + content_type nằm trên đó). Usecase tiêu thụ
    # một lần, không buffer vào RAM.
    source: UploadStream
    tenant_id: str | None = None
