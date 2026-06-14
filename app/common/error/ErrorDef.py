# Immutable descriptor of a single catalog error code.
# Mô tả bất biến của một mã lỗi trong catalog.
from dataclasses import dataclass

import grpc

from app.common.error.Visibility import Visibility


@dataclass(frozen=True)
class ErrorDef:
    # errorKey = "E" + code zero-padded to the tier width (6 digits for Base Platform).
    # errorKey = "E" + code zero-pad theo độ rộng tầng (6 chữ số cho Base Platform).
    error_key: str
    code: int
    message: str
    http_status: int
    grpc_status: grpc.StatusCode
    visibility: Visibility
