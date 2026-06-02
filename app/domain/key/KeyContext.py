from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class KeyContext:
    key_id: str
    public_key: str
    algorithm: str
    activate_at: datetime
    expires_at: datetime
    is_deleted: bool = False

    def can_sign(self, now: datetime) -> bool:
        return not self.is_deleted and now >= self.activate_at

    def can_verify(self, now: datetime) -> bool:
        return not self.is_deleted and now < self.expires_at

    def is_active(self, now: datetime) -> bool:
        return self.can_verify(now)
