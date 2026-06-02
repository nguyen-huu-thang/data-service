import logging
from datetime import datetime, timezone

import jwt
from core.config.runtime import RuntimeConfig

from app.application.dto.auth.VerifiedClaims import VerifiedClaims
from app.common.exception.InvalidTokenException import InvalidTokenException
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
            raise InvalidTokenException(f"Malformed token header: {e}") from e

        kid = header.get("kid")
        if not kid:
            raise InvalidTokenException("Missing kid in token header")

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
                raise InvalidTokenException("Cannot resolve verification key") from e

            key_ctx = self._cache.resolve(kid, now)

        if key_ctx is None:
            raise InvalidTokenException(f"Unknown or expired key: kid={kid}")

        try:
            payload = jwt.decode(
                token,
                key_ctx.public_key,
                algorithms=[key_ctx.algorithm],
                audience=self._service_id,
                issuer=_SIGNER_SERVICE_ID,
            )
        except jwt.ExpiredSignatureError as e:
            raise InvalidTokenException("Token has expired") from e
        except jwt.InvalidAudienceError as e:
            raise InvalidTokenException("Token audience mismatch") from e
        except jwt.InvalidIssuerError as e:
            raise InvalidTokenException("Token issuer mismatch") from e
        except jwt.PyJWTError as e:
            raise InvalidTokenException(f"Token verification failed: {e}") from e

        sub = payload.get("sub")
        if not sub:
            raise InvalidTokenException("Missing sub claim")

        token_version = payload.get("token_version")
        if token_version is None:
            raise InvalidTokenException("Missing token_version claim")

        try:
            identity_id = bytes.fromhex(sub)
        except ValueError as e:
            raise InvalidTokenException(f"Invalid sub format (expected hex): {e}") from e

        return VerifiedClaims(
            identity_id=identity_id,
            token_version=int(token_version),
        )
