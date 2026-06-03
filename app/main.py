from xime import Application

from app.api.grpc.GrpcAdapter import GrpcAdapter
from app.api.rest.RestAdapter import RestAdapter

app = Application(config_module="app.config.dependency")

if __name__ == "__main__":
    app.use(GrpcAdapter()).use(RestAdapter()).run()
