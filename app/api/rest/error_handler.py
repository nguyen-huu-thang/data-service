# Global REST exception handlers — registered via configure_exception_handlers
# in app/config/web.py. They render the platform-standard error body and redact
# non-public errors before they reach the browser.
# Handler lỗi REST toàn cục — đăng ký qua configure_exception_handlers trong
# app/config/web.py. Trả body lỗi chuẩn platform và che lỗi không-public trước
# khi tới browser.
import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.common.error.ErrorDef import ErrorDef
from app.common.error.Visibility import Visibility
from app.common.error.error_code import UNKNOWN, get_error
from app.common.error.redaction import Channel, redact_for_channel
from app.common.exception.AppException import AppException

_log = logging.getLogger(__name__)


def _body(ed: ErrorDef) -> dict:
    return {"errorKey": ed.error_key, "code": ed.code, "message": ed.message}


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    raw = get_error(exc.error_key)
    # Anything not safe for the client is logged in full with its real code.
    # Lỗi không an toàn cho client được log đầy đủ kèm mã thật.
    if raw.visibility is not Visibility.PUBLIC:
        _log.error("Non-public error on REST: %s", raw.error_key, exc_info=exc)
    out = redact_for_channel(raw, Channel.REST_EXTERNAL)
    return JSONResponse(status_code=out.http_status, content=_body(out))


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Last-resort net: never let a raw exception / stack trace reach the client.
    # Lưới cuối: không bao giờ để exception thô / stack trace lọt ra client.
    _log.error("Unhandled error on REST", exc_info=exc)
    return JSONResponse(status_code=UNKNOWN.http_status, content=_body(UNKNOWN))
