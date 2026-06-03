import logging

import app.config.web  # noqa: F401 — registers OpenAPI config at import time
from xime.adapters.web import WebAdapter, configure_controllers

_log = logging.getLogger(__name__)


class RestAdapter:
    """HTTP/REST adapter — wraps WebAdapter and registers controller packages.

    Usage in main.py:
        app.use(GrpcAdapter()).use(RestAdapter()).run()

    Adapters start concurrently — gRPC and REST listen on separate ports
    (configured via grpc.port and server.port in application.yml).
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
    ) -> None:
        configure_controllers(
            "app.api.rest.external.object",
            "app.api.rest.external.version",
        )
        self._web = WebAdapter(host=host, port=port)

    async def start(self, app) -> None:
        _log.info("Starting REST adapter...")
        await self._web.start(app)

    async def stop(self) -> None:
        await self._web.stop()
