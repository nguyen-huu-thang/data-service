"""
Unit tests — REST exception handlers render the standard body and redact.
"""
import json

import pytest

from app.api.rest.error_handler import app_exception_handler, unhandled_exception_handler
from app.common.exception.AppException import PrivateError, PublicError, SystemError

pytestmark = pytest.mark.asyncio


async def test_public_error_full_body():
    resp = await app_exception_handler(None, PublicError("E067000"))
    assert resp.status_code == 404
    assert json.loads(resp.body) == {
        "errorKey": "E067000",
        "code": 67000,
        "message": "Không tìm thấy object",
    }


async def test_private_error_redacted_to_unknown():
    resp = await app_exception_handler(None, PrivateError("E060000"))
    assert resp.status_code == 500
    assert json.loads(resp.body)["errorKey"] == "E000000"


async def test_system_error_redacted_to_common_public():
    resp = await app_exception_handler(None, SystemError("E004003"))
    body = json.loads(resp.body)
    # UNAUTHENTICATED family, never leaks the SYSTEM key to a browser.
    assert body["errorKey"] == "E007002"


async def test_unhandled_exception_returns_e000000():
    resp = await unhandled_exception_handler(None, RuntimeError("boom"))
    assert resp.status_code == 500
    assert json.loads(resp.body)["errorKey"] == "E000000"
