from xime import Application
from xime.adapters.grpc import GrpcAdapter
from xime.adapters.web import WebAdapter

import app.config.web   # noqa: F401 — side-effect: registers REST controllers + OpenAPI
import app.config.grpc  # noqa: F401 — side-effect: registers gRPC services

app = Application()

if __name__ == "__main__":
    app.use(WebAdapter()).use(GrpcAdapter()).run()
