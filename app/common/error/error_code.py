# Central error catalog for Data Service.
# Catalog mã lỗi tập trung của Data Service.
#
# Platform standard: D:\code\xime\giới thiệu\.claude\docs\cross-cutting\
#   quy-uoc-ma-loi-va-exception.md
#
# Ranges:
#   - common  000000 - 009999  (shared by every service; also used when redacting)
#   - data    060000 - 069999  (this service's own block)
# Each block splits into three visibility zones by the thousands digit of the offset:
#   Private 0xxx-3xxx | System 4xxx-6xxx | Public 7xxx-9xxx.
#
# Dải mã:
#   - common  000000 - 009999  (dùng chung mọi service; cũng là mã che lỗi generic)
#   - data    060000 - 069999  (block riêng của service này)
# Mỗi block chia 3 vùng visibility theo chữ số hàng nghìn của offset:
#   Private 0xxx-3xxx | System 4xxx-6xxx | Public 7xxx-9xxx.
import grpc

from app.common.error.ErrorDef import ErrorDef
from app.common.error.Visibility import Visibility

_P = Visibility.PRIVATE
_S = Visibility.SYSTEM
_U = Visibility.PUBLIC


def _d(error_key: str, code: int, message: str, http: int, grpc_status: grpc.StatusCode, vis: Visibility) -> ErrorDef:
    return ErrorDef(error_key, code, message, http, grpc_status, vis)


# fmt: off
_CATALOG: tuple[ErrorDef, ...] = (
    # ── Common — Private (000000-003999): hạ tầng, không bao giờ ra ngoài ──
    _d("E000000", 0, "Lỗi không xác định",      500, grpc.StatusCode.INTERNAL, _P),
    _d("E000001", 1, "Lỗi nội bộ hệ thống",     500, grpc.StatusCode.INTERNAL, _P),
    _d("E000002", 2, "Lỗi cơ sở dữ liệu",       500, grpc.StatusCode.INTERNAL, _P),
    _d("E000003", 3, "Lỗi cấu hình",            500, grpc.StatusCode.INTERNAL, _P),

    # ── Common — System (004000-006999): liên service, chỉ service nội bộ đọc ──
    _d("E004000", 4000, "Lỗi gọi service nội bộ",            502, grpc.StatusCode.INTERNAL,          _S),
    _d("E004001", 4001, "Service phụ thuộc không khả dụng",  503, grpc.StatusCode.UNAVAILABLE,        _S),
    _d("E004002", 4002, "Hết thời gian chờ service nội bộ",  504, grpc.StatusCode.DEADLINE_EXCEEDED,  _S),
    _d("E004003", 4003, "Xác thực liên service thất bại",    401, grpc.StatusCode.UNAUTHENTICATED,    _S),

    # ── Common — Public (007000-009999): an toàn cho browser ──
    _d("E007000", 7000, "Yêu cầu không hợp lệ",          400, grpc.StatusCode.INVALID_ARGUMENT,     _U),
    _d("E007001", 7001, "Dữ liệu đầu vào không hợp lệ",   400, grpc.StatusCode.INVALID_ARGUMENT,     _U),
    _d("E007002", 7002, "Chưa xác thực",                 401, grpc.StatusCode.UNAUTHENTICATED,      _U),
    _d("E007003", 7003, "Phiên làm việc đã hết hạn",      401, grpc.StatusCode.UNAUTHENTICATED,      _U),
    _d("E007004", 7004, "Không có quyền truy cập",        403, grpc.StatusCode.PERMISSION_DENIED,    _U),
    _d("E007005", 7005, "Không tìm thấy tài nguyên",      404, grpc.StatusCode.NOT_FOUND,            _U),
    _d("E007006", 7006, "Tài nguyên đã tồn tại",          409, grpc.StatusCode.ALREADY_EXISTS,       _U),
    _d("E007007", 7007, "Vi phạm ràng buộc nghiệp vụ",    422, grpc.StatusCode.FAILED_PRECONDITION,  _U),
    _d("E007008", 7008, "Quá nhiều yêu cầu",              429, grpc.StatusCode.RESOURCE_EXHAUSTED,   _U),

    # ── Data — Private (060000-063999): nội bộ Data Service ──
    _d("E060000", 60000, "Lỗi nội bộ Data Service",                 500, grpc.StatusCode.INTERNAL, _P),
    _d("E060001", 60001, "Shard không hợp lệ hoặc không xác định",   500, grpc.StatusCode.INTERNAL, _P),
    _d("E060002", 60002, "Lỗi lưu trữ blob",                        500, grpc.StatusCode.INTERNAL, _P),

    # ── Data — Public (067000-069999): browser xem được ──
    _d("E067000", 67000, "Không tìm thấy object",                       404, grpc.StatusCode.NOT_FOUND,           _U),
    _d("E067001", 67001, "Object đã bị xóa",                            409, grpc.StatusCode.FAILED_PRECONDITION, _U),
    _d("E067002", 67002, "Trạng thái object không hợp lệ cho thao tác này", 409, grpc.StatusCode.FAILED_PRECONDITION, _U),
)
# fmt: on

ERROR_CODES: dict[str, ErrorDef] = {d.error_key: d for d in _CATALOG}

# Fallback when an unknown key is looked up — never raises, always returns a def.
# Mã dự phòng khi tra key lạ — không raise, luôn trả về một ErrorDef.
UNKNOWN = ERROR_CODES["E000000"]


def get_error(error_key: str) -> ErrorDef:
    return ERROR_CODES.get(error_key, UNKNOWN)


# Common Public code that an adapter falls back to when redacting a higher-security
# error toward a less-trusted channel, matched by gRPC status family (mục 9).
# Mã Public common mà adapter dùng khi che lỗi bảo mật cao hơn ra kênh kém tin cậy,
# khớp theo họ gRPC status (mục 9).
_GENERIC_BY_GRPC: dict[grpc.StatusCode, str] = {
    grpc.StatusCode.INVALID_ARGUMENT:    "E007001",
    grpc.StatusCode.UNAUTHENTICATED:     "E007002",
    grpc.StatusCode.PERMISSION_DENIED:   "E007004",
    grpc.StatusCode.NOT_FOUND:           "E007005",
    grpc.StatusCode.ALREADY_EXISTS:      "E007006",
    grpc.StatusCode.FAILED_PRECONDITION: "E007007",
    grpc.StatusCode.RESOURCE_EXHAUSTED:  "E007008",
}


def generic_for(ed: ErrorDef) -> ErrorDef:
    """Common Public code in the same status family — used to redact a SYSTEM
    error down to a browser. PRIVATE errors are redacted to E000000 by the caller.
    Mã Public common cùng họ status — dùng khi che một lỗi SYSTEM ra browser.
    Lỗi PRIVATE do bên gọi quy về E000000."""
    return get_error(_GENERIC_BY_GRPC.get(ed.grpc_status, "E007000"))
