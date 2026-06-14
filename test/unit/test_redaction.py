"""
Unit tests — channel redaction (the security-critical part of the standard).

  - PRIVATE  -> collapsed to E000000 on every outbound channel
  - SYSTEM   -> passes on gRPC (service-to-service), redacted on REST
  - PUBLIC   -> passes on every channel
"""
from app.domain.error.Channel import Channel
from app.domain.error.error_code import get_error
from app.domain.error.redaction import redact_for_channel
from app.domain.error.Visibility import Visibility

_PRIVATE = get_error("E060000")  # data Private, INTERNAL
_SYSTEM = get_error("E004003")   # common System, UNAUTHENTICATED
_PUBLIC = get_error("E067000")   # data Public, NOT_FOUND


def test_private_redacted_on_rest():
    out = redact_for_channel(_PRIVATE, Channel.REST_EXTERNAL)
    assert out.error_key == "E000000"


def test_private_redacted_on_grpc():
    out = redact_for_channel(_PRIVATE, Channel.GRPC_INTERNAL)
    assert out.error_key == "E000000"


def test_system_passes_on_grpc():
    out = redact_for_channel(_SYSTEM, Channel.GRPC_INTERNAL)
    assert out.error_key == _SYSTEM.error_key
    assert out.visibility is Visibility.SYSTEM


def test_system_redacted_on_rest_to_common_public():
    out = redact_for_channel(_SYSTEM, Channel.REST_EXTERNAL)
    # UNAUTHENTICATED family -> common public E007002, never leaks the SYSTEM key.
    assert out.error_key == "E007002"
    assert out.visibility is Visibility.PUBLIC


def test_public_passes_on_rest():
    out = redact_for_channel(_PUBLIC, Channel.REST_EXTERNAL)
    assert out.error_key == _PUBLIC.error_key


def test_public_passes_on_grpc():
    out = redact_for_channel(_PUBLIC, Channel.GRPC_INTERNAL)
    assert out.error_key == _PUBLIC.error_key
