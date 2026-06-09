"""
Unit tests — JwtVerificationService:
  - valid token → VerifiedClaims returned
  - expired token → InvalidTokenException
  - wrong audience → InvalidTokenException
  - wrong issuer → InvalidTokenException
  - unknown kid (cache miss, Trust sync, still not found) → InvalidTokenException
  - cache miss → sync from Trust → verify succeeds
  - malformed token → InvalidTokenException
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.application.service.authorization.JwtVerificationService import JwtVerificationService
from app.common.exception.InvalidTokenException import InvalidTokenException
from app.domain.trust.VerificationKeyRecord import VerificationKeyRecord
from app.integration.trust.key.VerificationKeyCache import VerificationKeyCache

pytestmark = pytest.mark.asyncio

_KID        = "test-key-1"
_SERVICE_ID = "data-service"
_ISSUER     = "identity"
_IDENTITY   = b'\xAB' * 24


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rsa_key():
    return rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )


def _public_pem(private_key) -> str:
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()


def _make_token(
    private_key,
    *,
    kid: str = _KID,
    aud: str = _SERVICE_ID,
    iss: str = _ISSUER,
    exp_delta: timedelta = timedelta(hours=1),
    sub: str = _IDENTITY.hex(),
) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": sub,
            "aud": aud,
            "iss": iss,
            "token_version": 1,
            "exp": now + exp_delta,
            "iat": now,
        },
        private_key,
        algorithm="RS256",
        headers={"kid": kid},
    )


def _make_key_record(private_key, kid: str = _KID) -> VerificationKeyRecord:
    now = datetime.now(timezone.utc)
    return VerificationKeyRecord(
        key_id=kid,
        verifier_service_id=_SERVICE_ID,
        public_key=_public_pem(private_key),
        algorithm="RS256",
        key_size=2048,
        activate_at=now - timedelta(hours=1),
        expires_at=now + timedelta(hours=24),
    )


def _build_service(
    key_record: VerificationKeyRecord | None,
    trust_returns: list[VerificationKeyRecord] | None = None,
) -> JwtVerificationService:
    cache = VerificationKeyCache()
    if key_record is not None:
        cache.update([key_record])

    trust = MagicMock()
    trust.fetch_verification_keys = AsyncMock(return_value=trust_returns or [])

    config = MagicMock()
    config.get.return_value = _SERVICE_ID

    return JwtVerificationService(cache, trust, config)


# ── Tests ─────────────────────────────────────────────────────────────────────

async def test_valid_token_returns_correct_claims():
    priv = _rsa_key()
    ctx  = _make_key_record(priv)
    svc  = _build_service(ctx)

    claims = await svc.verify(_make_token(priv))

    assert claims.identity_id == _IDENTITY
    assert claims.token_version == 1


async def test_expired_token_raises_invalid_token():
    priv = _rsa_key()
    svc  = _build_service(_make_key_record(priv))

    with pytest.raises(InvalidTokenException, match="expired"):
        await svc.verify(_make_token(priv, exp_delta=-timedelta(hours=1)))


async def test_wrong_audience_raises_invalid_token():
    priv = _rsa_key()
    svc  = _build_service(_make_key_record(priv))

    with pytest.raises(InvalidTokenException, match="audience"):
        await svc.verify(_make_token(priv, aud="wrong-service"))


async def test_wrong_issuer_raises_invalid_token():
    priv = _rsa_key()
    svc  = _build_service(_make_key_record(priv))

    with pytest.raises(InvalidTokenException, match="issuer"):
        await svc.verify(_make_token(priv, iss="wrong-issuer"))


async def test_unknown_kid_syncs_trust_then_raises():
    priv = _rsa_key()
    # Cache is empty AND Trust returns nothing → unknown key
    svc  = _build_service(None, trust_returns=[])

    with pytest.raises(InvalidTokenException, match="Unknown or expired key"):
        await svc.verify(_make_token(priv, kid="no-such-key"))

    # Trust must have been called exactly once
    svc._trust.fetch_verification_keys.assert_called_once()


async def test_cache_miss_syncs_trust_and_verifies():
    priv = _rsa_key()
    ctx  = _make_key_record(priv)
    # Start with empty cache; Trust returns the key
    svc  = _build_service(None, trust_returns=[ctx])

    claims = await svc.verify(_make_token(priv))

    assert claims.identity_id == _IDENTITY
    svc._trust.fetch_verification_keys.assert_called_once()


async def test_malformed_token_raises_invalid_token():
    priv = _rsa_key()
    svc  = _build_service(_make_key_record(priv))

    with pytest.raises(InvalidTokenException, match="Malformed"):
        await svc.verify("not-a-jwt-at-all")


async def test_missing_sub_claim_raises():
    priv   = _rsa_key()
    record = _make_key_record(priv)
    cache  = VerificationKeyCache()
    cache.update([record])

    now = datetime.now(timezone.utc)
    token = jwt.encode(
        # sub is intentionally omitted
        {"aud": _SERVICE_ID, "iss": _ISSUER, "token_version": 1,
         "exp": now + timedelta(hours=1)},
        priv,
        algorithm="RS256",
        headers={"kid": _KID},
    )

    trust  = MagicMock()
    config = MagicMock()
    config.get.return_value = _SERVICE_ID
    svc = JwtVerificationService(cache, trust, config)

    with pytest.raises(InvalidTokenException, match="sub"):
        await svc.verify(token)
