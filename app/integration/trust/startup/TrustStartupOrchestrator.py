import logging

from app.integration.trust.certificate.TrustCertificateSynchronizer import TrustCertificateSynchronizer
from app.integration.trust.key.VerificationKeySynchronizer import VerificationKeySynchronizer
from app.integration.trust.publicca.TrustRootCertificateInitializer import TrustRootCertificateInitializer
from app.integration.trust.ssl.GrpcServerSslContextProvider import GrpcServerSslContextProvider

_log = logging.getLogger(__name__)


class TrustStartupOrchestrator:
    """
    Runs the full trust bootstrap sequence at application startup.

    Ordering is strict:
      1. Load root CA certificate from disk       → enables cert + key verification
      2. Synchronize mTLS certificate              → establishes outbound mTLS identity
      3. Build server SSL credentials              → enables inbound mTLS connections
      4. Synchronize verification keys             → enables JWT signature verification
    """

    def __init__(
        self,
        root_ca_init: TrustRootCertificateInitializer,
        cert_sync: TrustCertificateSynchronizer,
        server_ssl: GrpcServerSslContextProvider,
        key_sync: VerificationKeySynchronizer,
    ) -> None:
        self._root_ca_init = root_ca_init
        self._cert_sync = cert_sync
        self._server_ssl = server_ssl
        self._key_sync = key_sync

    async def post_construct(self) -> None:
        _log.info("Trust startup: loading root CA certificate.")
        self._root_ca_init.initialize()

        _log.info("Trust startup: synchronizing mTLS certificate.")
        await self._cert_sync.synchronize_on_startup()

        _log.info("Trust startup: building server SSL credentials.")
        self._server_ssl.reload()

        _log.info("Trust startup: synchronizing verification keys.")
        await self._key_sync.synchronize()

        _log.info("Trust startup complete.")
