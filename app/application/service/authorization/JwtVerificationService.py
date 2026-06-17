import logging
from datetime import datetime, timezone

import jwt
from xime.core.config.runtime import RuntimeConfig

from app.application.dto.auth.VerifiedClaims import VerifiedClaims
from app.common.exception.AppException import PublicError
from app.domain.sharedkernel.service.IdService import IdService
from app.integration.trust.key.TrustKeyClient import TrustKeyClient
from app.integration.trust.key.VerificationKeyCache import VerificationKeyCache

_log = logging.getLogger(__name__)

_SIGNER_SERVICE_ID = "identity"


class JwtVerificationService:
    def __init__(
        self,
        key_cache: VerificationKeyCache,
        trust_key_client: TrustKeyClient,
        config: RuntimeConfig,
    ) -> None:
        self._cache = key_cache
        self._trust = trust_key_client
        # trust.service_id matches the verifier_service_id registered with Trust Service
        self._service_id: str = config.get("trust.service_id", "data-service")

    async def verify(self, token: str) -> VerifiedClaims:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.DecodeError as e:
            raise PublicError("E007002",f"Malformed token header: {e}") from e

        kid = header.get("kid")
        if not kid:
            raise PublicError("E007002","Missing kid in token header")

        now = datetime.now(timezone.utc)
        key_ctx = self._cache.resolve(kid, now)

        if key_ctx is None:
            # Cache miss — sync from Trust Service and retry once
            try:
                keys = await self._trust.fetch_verification_keys(
                    signer_service_id=_SIGNER_SERVICE_ID,
                    verifier_service_id=self._service_id,
                )
                self._cache.update(keys)
            except Exception as e:
                _log.error("Failed to sync verification keys from Trust Service: %s", e)
                raise PublicError("E007002","Cannot resolve verification key") from e

            key_ctx = self._cache.resolve(kid, now)

        if key_ctx is None:
            raise PublicError("E007002",f"Unknown or expired key: kid={kid}")

        try:
            payload = jwt.decode(
                token,
                key_ctx.public_key,
                algorithms=[key_ctx.algorithm],
                audience=self._service_id,
                issuer=_SIGNER_SERVICE_ID,
            )
        except jwt.ExpiredSignatureError as e:
            raise PublicError("E007003", "Token has expired") from e
        except jwt.InvalidAudienceError as e:
            raise PublicError("E007002","Token audience mismatch") from e
        except jwt.InvalidIssuerError as e:
            raise PublicError("E007002","Token issuer mismatch") from e
        except jwt.PyJWTError as e:
            raise PublicError("E007002",f"Token verification failed: {e}") from e

        sub = payload.get("sub")
        if not sub:
            raise PublicError("E007002","Missing sub claim")

        token_version = payload.get("token_version")
        if token_version is None:
            raise PublicError("E007002","Missing token_version claim")

        # sub carries the identity id as a Base62 string (platform-wide string-ID
        # convention, same as REST path params).
        # sub mang identity id dạng chuỗi Base62 (chuẩn string-ID toàn platform,
        # giống path param REST).
        try:
            identity_id = IdService.from_string(sub)
        except ValueError as e:
            raise PublicError("E007002",f"Invalid sub format (expected Base62): {e}") from e

        subject_type = payload.get("subject_type", "HUMAN")
        name = payload.get("name", "")

        return VerifiedClaims(
            identity_id=identity_id,
            token_version=int(token_version),
            subject_type=subject_type,
            name=name,
        )
