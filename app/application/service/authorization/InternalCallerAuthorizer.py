from xime.core.config.runtime import RuntimeConfig

from app.common.exception.AppException import SystemError


class InternalCallerAuthorizer:
    """Authorize a service-to-service caller on the internal gRPC endpoints.

    Internal endpoints (e.g. PurgeObject) are reachable only over mTLS. The
    verified peer Common Name - taken from the client certificate by the
    framework gRPC interceptor and read via `current_caller()` - must appear in
    the configured allowlist `grpc.internal.allowed_callers`. Fail-closed: an
    empty allowlist denies every caller, so a misconfiguration can never silently
    expose a destructive internal endpoint.

    Authorize caller service-to-service trên endpoint gRPC nội bộ. Endpoint nội bộ
    (vd PurgeObject) chỉ tới được qua mTLS. CN của peer đã verify (framework lấy từ
    client cert, đọc qua `current_caller()`) phải nằm trong allowlist cấu hình
    `grpc.internal.allowed_callers`. Fail-closed: allowlist rỗng từ chối mọi caller
    nên cấu hình sai không bao giờ vô tình phơi endpoint nội bộ nguy hiểm.

    The policy only depends on the configured allowlist; the caller CN is passed
    in so the class stays free of any ambient request-context coupling and is easy
    to unit test. The transport (gRPC handler) resolves the CN and passes it here.
    Policy chỉ phụ thuộc allowlist cấu hình; CN của caller được truyền vào để class
    không dính ngữ cảnh request và dễ unit test. Tầng transport (handler gRPC) phân
    giải CN rồi truyền vào đây.
    """

    def __init__(self, config: RuntimeConfig) -> None:
        callers = config.get("grpc.internal.allowed_callers", []) or []
        self._allowed: frozenset[str] = frozenset(callers)

    def authorize(self, caller_cn: str | None) -> str:
        # No verified mTLS peer — the call did not present a valid client cert
        # (or did not arrive over mTLS at all).
        # Không có peer mTLS đã verify - call không kèm client cert hợp lệ (hoặc
        # không đi qua mTLS).
        if not caller_cn:
            raise SystemError("E004003")
        # Peer verified but not on the allowlist for internal operations.
        # Peer đã verify nhưng không nằm trong allowlist cho thao tác nội bộ.
        if caller_cn not in self._allowed:
            raise SystemError("E064000")
        return caller_cn
