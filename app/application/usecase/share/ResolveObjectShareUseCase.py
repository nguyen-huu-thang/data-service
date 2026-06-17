from datetime import datetime, timezone

from app.application.dto.share.ResolveObjectShareQuery import ResolveObjectShareQuery
from app.application.port.outbound.object.LoadObjectPort import LoadObjectPort
from app.application.port.outbound.share.ObjectShareRepository import ObjectShareRepository
from app.common.exception.AppException import PublicError
from app.domain.object.model.DataObject import DataObject
from app.domain.object.valueobject.ObjectStatus import ObjectStatus


class ResolveObjectShareUseCase:
    """
    Resolve a share token to its object. The token is the authorization, so no
    JWT is required; an expired/unknown token or unavailable object yields the
    same not-found error (no information leak).

    Resolve share token -> object. Token chính là phần xác thực nên không cần
    JWT; token hết hạn/không tồn tại hoặc object không khả dụng đều trả cùng lỗi
    not-found (không rò rỉ thông tin).
    """

    def __init__(
        self,
        load_object: LoadObjectPort,
        share_repository: ObjectShareRepository,
    ) -> None:
        self._load = load_object
        self._share = share_repository

    async def execute(self, query: ResolveObjectShareQuery) -> DataObject:
        now = datetime.now(timezone.utc)

        share = await self._share.find_by_token(query.token)
        if share is None or share.is_expired(now):
            raise PublicError("E067000")

        obj = await self._load.find_by_id(share.object_id)
        if obj is None or obj.status in (ObjectStatus.PURGED, ObjectStatus.SOFT_DELETED):
            raise PublicError("E067000")

        return obj
