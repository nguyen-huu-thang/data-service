from dataclasses import dataclass

from app.application.dto.upload.UploadStream import UploadStream
from app.domain.sharedkernel.model.Id import Id


@dataclass(frozen=True)
class CreateVersionCommand:
    requester_identity_id: Id
    requester_subject_type: str
    requester_name: str
    object_id: Id
    # Streaming source of the new version's blob (filename + content_type on it).
    # Nguồn stream của blob version mới (filename + content_type nằm trên đó).
    source: UploadStream
