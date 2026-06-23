"""
Unit tests — TrustKeyL2Cache:
  - JSON round-trip preserves the verification key records
  - empty cache → None
  - Redis errors are fail-soft: load() → None, store() never raises
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.trust.VerificationKeyRecord import VerificationKeyRecord
from app.integration.trust.key.TrustKeyL2Cache import TrustKeyL2Cache
from test.conftest import mock_runtime_config

pytestmark = pytest.mark.asyncio


def _record(kid: str = "k1") -> VerificationKeyRecord:
    now = datetime.now(timezone.utc)
    return VerificationKeyRecord(
        key_id=kid,
        verifier_service_id="data-service",
        public_key="-----BEGIN PUBLIC KEY-----\nXXX\n-----END PUBLIC KEY-----",
        algorithm="RS256",
        key_size=2048,
        activate_at=now - timedelta(hours=1),
        expires_at=now + timedelta(hours=1),
    )


def _cache_mock() -> MagicMock:
    store: dict[str, bytes] = {}
    cache = MagicMock()
    cache.get = AsyncMock(side_effect=lambda k: store.get(k))

    async def _set(k, v, ttl=None):
        store[k] = v

    cache.set = AsyncMock(side_effect=_set)
    return cache


async def test_round_trip_preserves_records():
    l2 = TrustKeyL2Cache(_cache_mock(), mock_runtime_config())
    records = [_record("k1"), _record("k2")]

    await l2.store(records)
    loaded = await l2.load()

    assert loaded == records


async def test_load_returns_none_when_empty():
    l2 = TrustKeyL2Cache(_cache_mock(), mock_runtime_config())
    assert await l2.load() is None


async def test_load_fail_soft_on_cache_error():
    cache = MagicMock()
    cache.get = AsyncMock(side_effect=RuntimeError("redis down"))
    l2 = TrustKeyL2Cache(cache, mock_runtime_config())

    # Must not raise — auth falls back to Trust.
    assert await l2.load() is None


async def test_store_fail_soft_on_cache_error():
    cache = MagicMock()
    cache.set = AsyncMock(side_effect=RuntimeError("redis down"))
    l2 = TrustKeyL2Cache(cache, mock_runtime_config())

    # Must not raise — a failed write is ignored.
    await l2.store([_record()])


async def test_uses_configured_ttl_on_store():
    cache = _cache_mock()
    l2 = TrustKeyL2Cache(cache, mock_runtime_config(**{"trust.verification_key_l2_ttl_seconds": 120}))

    await l2.store([_record()])

    assert cache.set.call_args.kwargs["ttl"] == 120
