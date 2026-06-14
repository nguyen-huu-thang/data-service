"""
Integration-style test — AppExceptionInterceptor over a real in-process gRPC
server, wired in the same order the framework uses: the built-in
ErrorMappingInterceptor is prepended (outermost) and ours is appended (innermost).

Proves the end-to-end contract:
  - PublicError  -> its real status + xime-error / xime-error-code metadata
  - PrivateError -> redacted to INTERNAL / E000000 (no internal key leaks)
  - plain Exception -> INTERNAL / E000000
"""
import grpc
import grpc.aio
import pytest

from xime.adapters.grpc.interceptors._error import ErrorMappingInterceptor

from app.api.grpc.interceptor.AppExceptionInterceptor import AppExceptionInterceptor
from app.common.exception.AppException import PrivateError, PublicError

pytestmark = pytest.mark.asyncio

_METHOD = "/probe.Probe/Call"


def _generic_handler(raiser):
    async def handler(request, context):
        raiser()
        return b""

    handlers = {
        "Call": grpc.unary_unary_rpc_method_handler(
            handler,
            request_deserializer=lambda b: b,
            response_serializer=lambda b: b,
        )
    }
    return grpc.method_handlers_generic_handler("probe.Probe", handlers)


async def _call(raiser):
    # Mirror framework ordering: built-ins (outermost) then ours (innermost).
    server = grpc.aio.server(interceptors=[ErrorMappingInterceptor({}), AppExceptionInterceptor()])
    server.add_generic_rpc_handlers((_generic_handler(raiser),))
    port = server.add_insecure_port("127.0.0.1:0")
    await server.start()
    try:
        async with grpc.aio.insecure_channel(f"127.0.0.1:{port}") as ch:
            call = ch.unary_unary(_METHOD, request_serializer=lambda b: b, response_deserializer=lambda b: b)
            with pytest.raises(grpc.aio.AioRpcError) as ei:
                await call(b"x")
            err = ei.value
            return err.code(), dict(err.trailing_metadata() or ())
    finally:
        await server.stop(None)


async def test_public_error_keeps_status_and_metadata():
    def raiser():
        raise PublicError("E067000")

    code, md = await _call(raiser)
    assert code is grpc.StatusCode.NOT_FOUND
    assert md.get("xime-error") == "E067000"
    assert md.get("xime-error-code") == "67000"


async def test_private_error_redacted():
    def raiser():
        raise PrivateError("E060000")

    code, md = await _call(raiser)
    assert code is grpc.StatusCode.INTERNAL
    assert md.get("xime-error") == "E000000"


async def test_plain_exception_redacted():
    def raiser():
        raise RuntimeError("boom")

    code, md = await _call(raiser)
    assert code is grpc.StatusCode.INTERNAL
    assert md.get("xime-error") == "E000000"
