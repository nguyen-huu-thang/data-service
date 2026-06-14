# Test helper: assert that a block raises an AppException carrying a specific
# errorKey. Replaces the old per-class `pytest.raises(SomeException)` now that all
# business errors share the three base classes and are distinguished by errorKey.
# Helper test: khẳng định block ném AppException mang đúng errorKey. Thay cho
# `pytest.raises(SomeException)` cũ, vì mọi lỗi nghiệp vụ nay dùng chung 3 base
# class và phân biệt nhau bằng errorKey.
from contextlib import contextmanager

import pytest

from app.common.exception.AppException import AppException


@contextmanager
def raises_app(error_key: str):
    with pytest.raises(AppException) as exc_info:
        yield exc_info
    actual = exc_info.value.error_key
    assert actual == error_key, f"expected errorKey {error_key}, got {actual}"
