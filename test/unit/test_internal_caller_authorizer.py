"""
Unit tests — InternalCallerAuthorizer:
  - CN on the allowlist → returns the CN
  - CN not on the allowlist → SystemError E064000 (not permitted)
  - no verified peer (None / empty) → SystemError E004003 (unauthenticated)
  - empty allowlist denies every caller (fail-closed)
"""
from unittest.mock import MagicMock

import pytest

from test._app_errors import raises_app

from app.application.service.authorization.InternalCallerAuthorizer import (
    InternalCallerAuthorizer,
)


def _authorizer(allowed: list[str]) -> InternalCallerAuthorizer:
    config = MagicMock()
    config.get.return_value = allowed
    return InternalCallerAuthorizer(config)


# ── Allowed ───────────────────────────────────────────────────────────────────

def test_returns_cn_when_allowed():
    authz = _authorizer(["application-service", "lifecycle-service"])
    assert authz.authorize("application-service") == "application-service"


# ── Denied — not on allowlist ─────────────────────────────────────────────────

def test_denies_caller_not_on_allowlist():
    authz = _authorizer(["application-service"])
    with raises_app("E064000"):
        authz.authorize("notification-service")


def test_empty_allowlist_denies_every_caller():
    authz = _authorizer([])
    with raises_app("E064000"):
        authz.authorize("application-service")


# ── Denied — no verified peer ─────────────────────────────────────────────────

def test_denies_when_no_peer_identity():
    authz = _authorizer(["application-service"])
    with raises_app("E004003"):
        authz.authorize(None)


def test_denies_when_peer_cn_empty_string():
    authz = _authorizer(["application-service"])
    with raises_app("E004003"):
        authz.authorize("")


# ── Config robustness ─────────────────────────────────────────────────────────

def test_handles_none_config_value_as_empty():
    # config.get may return None if the key is absent; treat it as empty (deny).
    config = MagicMock()
    config.get.return_value = None
    authz = InternalCallerAuthorizer(config)
    with raises_app("E064000"):
        authz.authorize("application-service")
