import threading
from datetime import datetime

from app.domain.key.KeyContext import KeyContext


class VerificationKeyCache:
    def __init__(self) -> None:
        self._cache: dict[str, KeyContext] = {}
        self._lock = threading.Lock()

    def resolve(self, key_id: str, now: datetime) -> KeyContext | None:
        key = self._cache.get(key_id)
        return key if key and key.can_verify(now) else None

    def update(self, keys: list[KeyContext]) -> None:
        with self._lock:
            for key in keys:
                self._cache[key.key_id] = key

    def clean_expired(self, now: datetime) -> None:
        with self._lock:
            self._cache = {k: v for k, v in self._cache.items() if v.can_verify(now)}
