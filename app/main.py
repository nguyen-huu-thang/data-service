from xime import Application
from xime.adapters.grpc import GrpcAdapter
from xime.adapters.web import WebAdapter


app = Application()

if __name__ == "__main__":
    app.use(WebAdapter()).use(GrpcAdapter()).run()
