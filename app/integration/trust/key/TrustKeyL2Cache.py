import json
import logging
from datetime import datetime

from xime.core.config.runtime import RuntimeConfig
from xime.starters.cache import CacheService

from app.domain.trust.VerificationKeyRecord import VerificationKeyRecord

_log = logging.getLogger(__name__)

# Single shared key holding the full verification-key set as JSON.
# Một key dùng chung giữ toàn bộ tập khóa xác thực dạng JSON.
_CACHE_KEY = "data-service:trust:verification-keys"


class TrustKeyL2Cache:
    """Shared L2 cache (Redis) for Trust verification keys.

    The in-process VerificationKeyCache is the hot-path L1. This L2 lets multiple
    data-service instances share keys already synced from Trust: a key rotated and
    fetched by one instance is reused by the others without each making its own
    Trust round-trip, and it survives a single instance restart.

    Every operation is fail-soft - if Redis is unreachable or the payload is
    corrupt, load() returns None and store() is a no-op - so the caller always
    falls back to the in-process cache + Trust. Redis therefore never becomes a
    hard dependency on the authentication hot path.

    Cache L2 chia sẻ (Redis) cho khóa xác thực Trust. L1 in-process là hot path;
    L2 cho nhiều instance dùng chung khóa đã sync từ Trust (đỡ mỗi instance tự gọi
    Trust, sống qua restart). Mọi thao tác fail-soft: Redis chết / payload hỏng ->
    load() trả None, store() no-op; caller luôn fallback L1 + Trust. Redis không
    bao giờ là hard dependency của hot path xác thực.
    """

    def __init__(self, cache: CacheService, config: RuntimeConfig) -> None:
        self._cache = cache
        self._ttl: int = int(config.get("trust.verification_key_l2_ttl_seconds", 3600))

    async def load(self) -> list[VerificationKeyRecord] | None:
        try:
            raw = await self._cache.get(_CACHE_KEY)
        except Exception as e:
            # Redis down / network error — fall back to Trust, never fail auth.
            # Redis chết / lỗi mạng - fallback Trust, không bao giờ làm fail auth.
            _log.debug("Trust key L2 read failed (fallback to Trust): %s", e)
            return None
        if not raw:
            return None
        try:
            return [self._decode(item) for item in json.loads(raw)]
        except Exception as e:
            _log.warning("Trust key L2 payload corrupt, ignoring: %s", e)
            return None

    async def store(self, keys: list[VerificationKeyRecord]) -> None:
        try:
            payload = json.dumps([self._encode(k) for k in keys]).encode()
            await self._cache.set(_CACHE_KEY, payload, ttl=self._ttl)
        except Exception as e:
            _log.debug("Trust key L2 write failed (ignored): %s", e)

    @staticmethod
    def _encode(k: VerificationKeyRecord) -> dict:
        return {
            "key_id": k.key_id,
            "verifier_service_id": k.verifier_service_id,
            "public_key": k.public_key,
            "algorithm": k.algorithm,
            "key_size": k.key_size,
            "activate_at": k.activate_at.isoformat(),
            "expires_at": k.expires_at.isoformat(),
        }

    @staticmethod
    def _decode(d: dict) -> VerificationKeyRecord:
        return VerificationKeyRecord(
            key_id=d["key_id"],
            verifier_service_id=d["verifier_service_id"],
            public_key=d["public_key"],
            algorithm=d["algorithm"],
            key_size=d["key_size"],
            activate_at=datetime.fromisoformat(d["activate_at"]),
            expires_at=datetime.fromisoformat(d["expires_at"]),
        )
