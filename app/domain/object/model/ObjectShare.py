from datetime import datetime


class ObjectShare:

    def __init__(
        self,
        share_id: bytes,
        object_id: bytes,
        share_token: str,
        expires_at: datetime | None,
        created_at: datetime,
    ) -> None:
        self._share_id = share_id

        self._object_id = object_id

        self._share_token = share_token

        self._expires_at = expires_at

        self._created_at = created_at

    @property
    def share_id(self) -> bytes:
        return self._share_id

    @property
    def object_id(self) -> bytes:
        return self._object_id

    @property
    def share_token(self) -> str:
        return self._share_token

    @property
    def expires_at(self) -> datetime | None:
        return self._expires_at

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def is_expired(
        self,
        now: datetime,
    ) -> bool:
        if self._expires_at is None:
            return False

        return now >= self._expires_at

    def never_expires(self) -> bool:
        return self._expires_at is None