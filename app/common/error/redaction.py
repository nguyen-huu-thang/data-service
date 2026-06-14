# Channel-based error redaction — enforces the visibility model at the adapter edge.
# Che lỗi theo kênh — thực thi mô hình visibility ngay ở rìa adapter.
from enum import Enum

from app.common.error.ErrorDef import ErrorDef
from app.common.error.Visibility import Visibility
from app.common.error.error_code import UNKNOWN, generic_for


class Channel(Enum):
    # Service-to-service over gRPC mTLS — SYSTEM and PUBLIC may pass through.
    # Liên service qua gRPC mTLS — SYSTEM và PUBLIC được phép lọt.
    GRPC_INTERNAL = 1

    # Browser / external REST — only PUBLIC may pass through.
    # Browser / REST ngoài — chỉ PUBLIC được phép lọt.
    REST_EXTERNAL = 2


def _is_allowed(visibility: Visibility, channel: Channel) -> bool:
    if channel is Channel.GRPC_INTERNAL:
        return visibility in (Visibility.SYSTEM, Visibility.PUBLIC)
    return visibility is Visibility.PUBLIC


def redact_for_channel(ed: ErrorDef, channel: Channel) -> ErrorDef:
    """Return the error to actually expose on `channel`.

    Allowed -> the original error. Otherwise PRIVATE collapses to E000000 and
    SYSTEM collapses to the common Public code in the same status family.
    Được phép -> lỗi gốc. Ngược lại: PRIVATE quy về E000000, SYSTEM quy về mã
    Public common cùng họ status.
    """
    if _is_allowed(ed.visibility, channel):
        return ed
    if ed.visibility is Visibility.PRIVATE:
        return UNKNOWN
    return generic_for(ed)
