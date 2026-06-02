from xime import Application

from app.api.grpc.GrpcAdapter import GrpcAdapter

app = Application(config_module="app.config.dependency")

if __name__ == "__main__":
    app.use(GrpcAdapter()).run()
