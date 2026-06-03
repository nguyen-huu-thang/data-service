import logging
from datetime import datetime, timezone

import grpc.aio
from xime.core.config.runtime import RuntimeConfig

from app.domain.key.KeyContext import KeyContext
from app.integration.trust.generated.trust_key_service_pb2 import GetVerificationKeysRequest
from app.integration.trust.generated.trust_key_service_pb2_grpc import KeyDistributionServiceStub

_log = logging.getLogger(__name__)


class TrustKeyClient:
    def __init__(self, config: RuntimeConfig) -> None:
        host = config.get("trust.grpc.host", "localhost")
        port = int(config.get("trust.grpc.port", 50052))
        # Channel is created at construction; managed for the lifetime of the service.
        # mTLS will be configured here in the future (see roadmap.md).
        self._channel = grpc.aio.insecure_channel(f"{host}:{port}")
        self._stub = KeyDistributionServiceStub(self._channel)

    async def pre_destroy(self) -> None:
        await self._channel.close()

    async def fetch_verification_keys(
        self,
        signer_service_id: str,
        verifier_service_id: str,
    ) -> list[KeyContext]:
        request = GetVerificationKeysRequest(
            signer_service_id=signer_service_id,
            verifier_service_id=verifier_service_id,
        )
        response = await self._stub.GetVerificationKeys(request)
        return [self._map_key(k) for k in response.keys]

    @staticmethod
    def _map_key(proto_key) -> KeyContext:
        return KeyContext(
            key_id=proto_key.key_id,
            public_key=proto_key.public_key,
            algorithm=proto_key.algorithm,
            activate_at=datetime.fromtimestamp(proto_key.activate_at_unix, tz=timezone.utc),
            expires_at=datetime.fromtimestamp(proto_key.expires_at_unix, tz=timezone.utc),
            is_deleted=proto_key.is_deleted,
        )
