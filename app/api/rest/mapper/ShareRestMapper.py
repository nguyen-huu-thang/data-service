from pydantic import BaseModel

from app.application.dto.share.CreateObjectShareResult import CreateObjectShareResult
from app.domain.object.model.ObjectShare import ObjectShare
from app.domain.sharedkernel.service.IdService import IdService


class CreateShareRequest(BaseModel):
    # ISO-8601 datetime, optional. Null → share never expires.
    expires_at: str | None = None


class CreateShareResponse(BaseModel):
    share_id: str
    share_token: str
    expires_at: str | None


class ShareResponse(BaseModel):
    share_id: str
    object_id: str
    share_token: str
    expires_at: str | None
    created_at: str


class ShareListResponse(BaseModel):
    shares: list[ShareResponse]


class ShareRestMapper:
    def to_create_response(self, result: CreateObjectShareResult) -> CreateShareResponse:
        return CreateShareResponse(
            share_id=IdService.to_string(result.share_id),
            share_token=result.share_token,
            expires_at=result.expires_at.isoformat() if result.expires_at is not None else None,
        )

    def to_share_response(self, share: ObjectShare) -> ShareResponse:
        return ShareResponse(
            share_id=IdService.to_string(share.share_id),
            object_id=IdService.to_string(share.object_id),
            share_token=share.share_token,
            expires_at=share.expires_at.isoformat() if share.expires_at is not None else None,
            created_at=share.created_at.isoformat(),
        )

    def to_list_response(self, shares: list[ObjectShare]) -> ShareListResponse:
        return ShareListResponse(shares=[self.to_share_response(s) for s in shares])
